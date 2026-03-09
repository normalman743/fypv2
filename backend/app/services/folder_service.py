from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func as sa_func

from app.models.folder import Folder
from app.models.course import Course
from app.models.file import File
from app.models.physical_file import PhysicalFile
from app.schemas.folder import CreateFolderRequest, UpdateFolderRequest
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


class FolderService:
    def __init__(self, db: Session):
        self.db = db

    def get_course_folders(self, course_id: int, user_id: int) -> List[Folder]:
        """Get all folders for a course (check course ownership)"""
        # Check if course exists and user has access
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()
        if not course:
            raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")

        return self.db.query(Folder).filter(Folder.course_id == course_id).all()

    def get_batch_folder_stats(self, folder_ids: list) -> Dict[int, dict]:
        """批量获取文件夹统计（一条 SQL 替代 N 条）"""
        if not folder_ids:
            return {}
        rows = (
            self.db.query(File.folder_id, sa_func.count(File.id))
            .filter(File.folder_id.in_(folder_ids))
            .group_by(File.folder_id)
            .all()
        )
        stats = {fid: {"file_count": cnt} for fid, cnt in rows}
        # 没有文件的文件夹也要返回 0
        for fid in folder_ids:
            if fid not in stats:
                stats[fid] = {"file_count": 0}
        return stats

    def get_course_folders_with_files(self, course_id: int, user_id: int) -> List[dict]:
        """一次性获取课程所有文件夹及其文件（替代 N+1 请求）"""
        # 校验课程权限
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()
        if not course:
            raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")

        # 一次查出所有文件夹
        folders = self.db.query(Folder).filter(Folder.course_id == course_id).all()
        folder_ids = [f.id for f in folders]

        # 一次查出所有文件（JOIN physical_file）
        files = []
        if folder_ids:
            files = (
                self.db.query(File)
                .options(joinedload(File.physical_file))
                .filter(File.folder_id.in_(folder_ids))
                .all()
            )

        # 按 folder_id 分组
        files_by_folder: Dict[int, list] = {fid: [] for fid in folder_ids}
        for f in files:
            if f.folder_id in files_by_folder:
                files_by_folder[f.folder_id].append(f)

        result = []
        for folder in folders:
            folder_files = files_by_folder.get(folder.id, [])
            result.append({
                "id": folder.id,
                "name": folder.name,
                "folder_type": folder.folder_type,
                "course_id": folder.course_id,
                "is_default": folder.is_default,
                "created_at": folder.created_at,
                "stats": {"file_count": len(folder_files)},
                "files": [
                    {
                        "id": file.id,
                        "original_name": file.original_name,
                        "file_type": file.file_type,
                        "file_size": file.physical_file.file_size if file.physical_file else 0,
                        "mime_type": file.physical_file.mime_type if file.physical_file else "unknown",
                        "course_id": file.course_id,
                        "folder_id": file.folder_id,
                        "user_id": file.user_id,
                        "is_processed": file.is_processed,
                        "processing_status": file.processing_status,
                        "created_at": file.created_at,
                    }
                    for file in folder_files
                ]
            })
        return result

    def create_folder(self, course_id: int, folder_data: CreateFolderRequest, user_id: int) -> Folder:
        """Create new folder in course"""
        # Check if course exists and user has access
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()
        if not course:
            raise NotFoundError("Course not found or access denied", "COURSE_NOT_FOUND")

        # Check if folder name already exists in this course
        existing = self.db.query(Folder).filter(
            Folder.course_id == course_id,
            Folder.name == folder_data.name
        ).first()
        if existing:
            raise BadRequestError(f"Folder name '{folder_data.name}' already exists in this course", "FOLDER_NAME_EXISTS")

        try:
            folder = Folder(
                name=folder_data.name,
                folder_type=folder_data.folder_type,
                course_id=course_id,
                is_default=False  # Only system can create default folders
            )
            self.db.add(folder)
            self.db.commit()
            self.db.refresh(folder)
            return folder
        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Failed to create folder", "FOLDER_CREATE_FAILED")

    def get_folder_stats(self, folder_id: int) -> dict:
        """Get folder statistics"""
        file_count = self.db.query(File).filter(File.folder_id == folder_id).count()
        return {
            "file_count": file_count
        }

    def update_folder(self, folder_id: int, folder_data: UpdateFolderRequest, user_id: int) -> Folder:
        """Update folder (check course ownership)"""
        # First check if folder exists
        folder = self.db.query(Folder).options(joinedload(Folder.course)).filter(Folder.id == folder_id).first()
        if not folder:
            raise NotFoundError("Folder not found", "FOLDER_NOT_FOUND")
        
        # Check if user owns the course
        if folder.course.user_id != user_id:
            raise ForbiddenError("You don't have permission to update this folder")

        # Check if trying to update name and it would conflict
        if folder_data.name and folder_data.name != folder.name:
            existing = self.db.query(Folder).filter(
                Folder.course_id == folder.course_id,
                Folder.name == folder_data.name,
                Folder.id != folder_id
            ).first()
            if existing:
                raise BadRequestError(f"Folder name '{folder_data.name}' already exists in this course", "FOLDER_NAME_EXISTS")

        try:
            # Only update provided fields
            update_data = folder_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(folder, field, value)

            self.db.commit()
            self.db.refresh(folder)
            return folder
        except IntegrityError:
            self.db.rollback()
            raise BadRequestError("Failed to update folder", "FOLDER_UPDATE_FAILED")

    def delete_folder(self, folder_id: int, user_id: int) -> bool:
        """Delete folder (check course ownership and if folder is empty)"""
        # First check if folder exists
        folder = self.db.query(Folder).options(joinedload(Folder.course)).filter(Folder.id == folder_id).first()
        if not folder:
            raise NotFoundError("Folder not found", "FOLDER_NOT_FOUND")
        
        # Check if user owns the course
        if folder.course.user_id != user_id:
            raise ForbiddenError("You don't have permission to delete this folder")

        # Check if folder is default (cannot be deleted)
        if folder.is_default:
            raise BadRequestError("Cannot delete default folder", "FOLDER_IS_DEFAULT")

        # Check if folder has files
        file_count = self.db.query(File).filter(File.folder_id == folder_id).count()
        if file_count > 0:
            raise BadRequestError("Cannot delete folder with files. Please delete all files first", "FOLDER_NOT_EMPTY")

        self.db.delete(folder)
        self.db.commit()
        return True