"""
存储管理相关的End-to-End工作流测试
"""
import pytest
import tempfile
from pathlib import Path
from .base import UserE2ETest
from .api_client import CampusLLMClient, APIException


@pytest.mark.storage
class TestFolderManagementWorkflow(UserE2ETest):
    """文件夹管理工作流测试"""
    
    @pytest.mark.smoke
    def test_complete_folder_lifecycle(self, client: CampusLLMClient, logged_in_user, 
                                     test_course):
        """完整的文件夹生命周期测试"""
        course_id = test_course["course"]["id"]
        
        # 1. 获取课程文件夹列表（应该包含默认文件夹）
        initial_response = client.get_course_folders(course_id)
        self.assert_success_response(initial_response)
        self.assert_folder_response(initial_response)
        
        initial_folders = initial_response["data"]["folders"]
        initial_count = len(initial_folders)
        
        # 2. 创建文件夹
        folder_data = {
            "name": "测试文件夹",
            "folder_type": "lecture"
        }
        create_response = client.create_folder(course_id, **folder_data)
        self.assert_success_response(create_response)
        self.assert_folder_response(create_response)
        
        folder_id = self.extract_id_from_response(create_response, "folder")
        
        # 3. 验证文件夹已创建
        folders_response = client.get_course_folders(course_id)
        folders = folders_response["data"]["folders"]
        assert len(folders) == initial_count + 1
        
        # 找到新创建的文件夹
        new_folder = next((f for f in folders if f["id"] == folder_id), None)
        assert new_folder is not None
        assert new_folder["name"] == folder_data["name"]
        assert new_folder["folder_type"] == folder_data["folder_type"]
        assert new_folder["course_id"] == course_id
        
        # 4. 更新文件夹
        update_data = {
            "name": "更新后的文件夹名称",
            "folder_type": "assignment"
        }
        update_response = client.update_folder(folder_id, **update_data)
        self.assert_success_response(update_response)
        
        # 验证更新是否生效
        updated_folders = client.get_course_folders(course_id)
        updated_folder = next((f for f in updated_folders["data"]["folders"] 
                             if f["id"] == folder_id), None)
        assert updated_folder["name"] == update_data["name"]
        assert updated_folder["folder_type"] == update_data["folder_type"]
        
        # 5. 获取文件夹文件列表（应该为空）
        files_response = client.get_folder_files(folder_id)
        self.assert_success_response(files_response)
        self.assert_file_response(files_response)
        
        files = files_response["data"]["files"]
        assert len(files) == 0
        
        # 6. 删除文件夹（空文件夹应该可以删除）
        delete_response = client.delete_folder(folder_id)
        self.assert_success_response(delete_response)
        
        # 验证删除是否生效
        final_folders = client.get_course_folders(course_id)
        folder_ids = [f["id"] for f in final_folders["data"]["folders"]]
        assert folder_id not in folder_ids
    
    def test_create_folder_with_different_types(self, client: CampusLLMClient, 
                                              logged_in_user, test_course):
        """创建不同类型的文件夹"""
        course_id = test_course["course"]["id"]
        folder_types = ["outline", "tutorial", "lecture", "exam", "assignment", "others"]
        
        created_folders = []
        
        for folder_type in folder_types:
            folder_data = {
                "name": f"测试{folder_type}文件夹",
                "folder_type": folder_type
            }
            
            response = client.create_folder(course_id, **folder_data)
            self.assert_success_response(response)
            
            folder_id = self.extract_id_from_response(response, "folder")
            created_folders.append(folder_id)
        
        # 验证所有文件夹都已创建
        folders_response = client.get_course_folders(course_id)
        folders = folders_response["data"]["folders"]
        
        for folder_type in folder_types:
            type_folders = [f for f in folders if f["folder_type"] == folder_type]
            assert len(type_folders) >= 1, f"No folder found for type {folder_type}"
    
    def test_create_folder_with_duplicate_name(self, client: CampusLLMClient, 
                                             logged_in_user, test_course):
        """创建重复名称的文件夹（应该允许）"""
        course_id = test_course["course"]["id"]
        folder_data = {
            "name": "重复名称测试",
            "folder_type": "lecture"
        }
        
        # 创建第一个文件夹
        response1 = client.create_folder(course_id, **folder_data)
        self.assert_success_response(response1)
        
        # 创建第二个同名文件夹（应该成功，因为通常允许同名文件夹）
        response2 = client.create_folder(course_id, **folder_data)
        self.assert_success_response(response2)
        
        # 验证两个文件夹都存在且ID不同
        folder_id1 = self.extract_id_from_response(response1, "folder")
        folder_id2 = self.extract_id_from_response(response2, "folder")
        assert folder_id1 != folder_id2
    
    def test_delete_default_folder(self, client: CampusLLMClient, logged_in_user, 
                                 test_course):
        """删除默认文件夹（应该失败）"""
        course_id = test_course["course"]["id"]
        
        # 获取文件夹列表，找到默认文件夹
        folders_response = client.get_course_folders(course_id)
        folders = folders_response["data"]["folders"]
        
        default_folder = next((f for f in folders if f.get("is_default", False)), None)
        
        if default_folder:
            # 尝试删除默认文件夹
            with pytest.raises(APIException) as exc_info:
                client.delete_folder(default_folder["id"])
            
            assert exc_info.value.status_code in [400, 403]


@pytest.mark.storage
class TestFileManagementWorkflow(UserE2ETest):
    """文件管理工作流测试"""
    
    @pytest.mark.smoke
    def test_complete_file_lifecycle(self, client: CampusLLMClient, logged_in_user,
                                   test_course, test_folder, temp_file):
        """完整的文件生命周期测试"""
        course_id = test_course["course"]["id"]
        folder_id = test_folder["folder"]["id"]
        
        # 1. 获取文件夹初始文件列表
        initial_files = client.get_folder_files(folder_id)
        initial_count = len(initial_files["data"]["files"])
        
        # 2. 上传文件
        upload_response = client.upload_file(
            file_path=temp_file,
            course_id=course_id,
            folder_id=folder_id,
            description="测试文件上传"
        )
        self.assert_success_response(upload_response)
        self.assert_file_response(upload_response)
        
        file_data = upload_response["data"]["file"]
        file_id = file_data["id"]
        
        # 验证文件信息
        assert file_data["original_name"] == temp_file.name
        assert file_data["course_id"] == course_id
        assert file_data["folder_id"] == folder_id
        
        # 3. 验证文件已上传
        files_response = client.get_folder_files(folder_id)
        files = files_response["data"]["files"]
        assert len(files) == initial_count + 1
        
        uploaded_file = next((f for f in files if f["id"] == file_id), None)
        assert uploaded_file is not None
        assert uploaded_file["original_name"] == temp_file.name
        
        # 4. 下载文件
        download_response = client.download_file(file_id)
        assert download_response.status_code == 200
        
        # 验证下载内容
        downloaded_content = download_response.content.decode('utf-8')
        with open(temp_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        assert downloaded_content == original_content
        
        # 5. 删除文件
        delete_response = client.delete_file(file_id)
        self.assert_success_response(delete_response)
        
        # 验证删除是否生效
        final_files = client.get_folder_files(folder_id)
        file_ids = [f["id"] for f in final_files["data"]["files"]]
        assert file_id not in file_ids
    
    def test_upload_different_file_types(self, client: CampusLLMClient, logged_in_user,
                                       test_course, test_folder, temp_image_file):
        """上传不同类型的文件"""
        course_id = test_course["course"]["id"]
        folder_id = test_folder["folder"]["id"]
        
        # 上传图片文件
        image_response = client.upload_file(
            file_path=temp_image_file,
            course_id=course_id,
            folder_id=folder_id,
            description="测试图片文件"
        )
        self.assert_success_response(image_response)
        
        image_data = image_response["data"]["file"]
        assert image_data["original_name"] == temp_image_file.name
        assert "png" in image_data["mime_type"].lower() or image_data["file_type"] == "png"
    
    def test_upload_large_file(self, client: CampusLLMClient, logged_in_user,
                             test_course, test_folder):
        """上传大文件测试"""
        course_id = test_course["course"]["id"]
        folder_id = test_folder["folder"]["id"]
        
        # 创建一个较大的临时文件（1MB）
        large_content = "大文件测试内容\n" * (1024 * 1024 // 20)  # 约1MB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                       encoding='utf-8') as f:
            f.write(large_content)
            large_file_path = Path(f.name)
        
        try:
            # 上传大文件
            upload_response = client.upload_file(
                file_path=large_file_path,
                course_id=course_id,
                folder_id=folder_id,
                description="大文件测试"
            )
            self.assert_success_response(upload_response)
            
            file_data = upload_response["data"]["file"]
            assert file_data["file_size"] > 1000000  # 大于1MB
            
        finally:
            # 清理临时文件
            if large_file_path.exists():
                large_file_path.unlink()
    
    def test_file_deduplication(self, client: CampusLLMClient, logged_in_user,
                              test_course, test_folder, temp_file):
        """文件去重测试"""
        course_id = test_course["course"]["id"]
        folder_id = test_folder["folder"]["id"]
        
        # 上传第一个文件
        response1 = client.upload_file(
            file_path=temp_file,
            course_id=course_id,
            folder_id=folder_id,
            description="第一次上传"
        )
        self.assert_success_response(response1)
        file1_data = response1["data"]["file"]
        
        # 上传相同内容的文件
        response2 = client.upload_file(
            file_path=temp_file,
            course_id=course_id,
            folder_id=folder_id,
            description="第二次上传"
        )
        self.assert_success_response(response2)
        file2_data = response2["data"]["file"]
        
        # 验证两个文件记录不同但可能共享物理存储
        assert file1_data["id"] != file2_data["id"]
        # 在去重系统中，physical_file_id 应该相同
        if "physical_file_id" in file1_data and "physical_file_id" in file2_data:
            assert file1_data["physical_file_id"] == file2_data["physical_file_id"]


@pytest.mark.storage
class TestTemporaryFileWorkflow(UserE2ETest):
    """临时文件工作流测试"""
    
    def test_temporary_file_lifecycle(self, client: CampusLLMClient, logged_in_user,
                                    temp_file):
        """临时文件生命周期测试"""
        # 1. 上传临时文件
        upload_response = client.upload_temporary_file(
            file_path=temp_file,
            expiry_hours=24,
            purpose="E2E测试临时文件"
        )
        self.assert_success_response(upload_response)
        
        temp_file_data = upload_response["data"]["file"]
        temp_file_id = temp_file_data["id"]
        
        # 验证临时文件信息
        assert temp_file_data["filename"] == temp_file.name
        assert temp_file_data["expires_at"] is not None
        
        # 2. 下载临时文件
        download_response = client.download_temporary_file(temp_file_id)
        assert download_response.status_code == 200
        
        # 验证下载内容
        downloaded_content = download_response.content.decode('utf-8')
        with open(temp_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        assert downloaded_content == original_content
        
        # 3. 删除临时文件
        delete_response = client.delete_temporary_file(temp_file_id)
        self.assert_success_response(delete_response)
        
        # 4. 验证删除后无法下载
        with pytest.raises(APIException) as exc_info:
            client.download_temporary_file(temp_file_id)
        
        self.assert_not_found_response(exc_info.value)
    
    def test_temporary_file_with_different_expiry(self, client: CampusLLMClient, 
                                                logged_in_user, temp_file):
        """不同过期时间的临时文件测试"""
        # 短期临时文件（1小时）
        short_response = client.upload_temporary_file(
            file_path=temp_file,
            expiry_hours=1,
            purpose="短期临时文件"
        )
        self.assert_success_response(short_response)
        
        # 长期临时文件（168小时 = 7天）
        long_response = client.upload_temporary_file(
            file_path=temp_file,
            expiry_hours=168,
            purpose="长期临时文件"
        )
        self.assert_success_response(long_response)
        
        # 验证过期时间不同
        short_expires = short_response["data"]["file"]["expires_at"]
        long_expires = long_response["data"]["file"]["expires_at"]
        assert short_expires != long_expires


@pytest.mark.storage
class TestStoragePermissions(UserE2ETest):
    """存储权限测试"""
    
    def test_access_other_user_folder(self, client: CampusLLMClient, logged_in_user,
                                    another_user, test_semester):
        """访问其他用户的文件夹"""
        # 另一个用户创建课程和文件夹
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        # 创建课程
        from .factories import create_test_course
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        course_id = self.extract_id_from_response(course_response, "course")
        
        # 创建文件夹
        folder_response = another_client.create_folder(course_id, 
                                                     name="其他用户文件夹", 
                                                     folder_type="lecture")
        folder_id = self.extract_id_from_response(folder_response, "folder")
        
        # 当前用户尝试访问其他用户的文件夹
        with pytest.raises(APIException) as exc_info:
            client.get_folder_files(folder_id)
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_upload_to_other_user_folder(self, client: CampusLLMClient, logged_in_user,
                                       another_user, test_semester, temp_file):
        """上传文件到其他用户的文件夹"""
        # 另一个用户创建课程和文件夹
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        from .factories import create_test_course
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        course_id = self.extract_id_from_response(course_response, "course")
        
        folder_response = another_client.create_folder(course_id, 
                                                     name="其他用户文件夹", 
                                                     folder_type="lecture")
        folder_id = self.extract_id_from_response(folder_response, "folder")
        
        # 当前用户尝试上传文件到其他用户的文件夹
        with pytest.raises(APIException) as exc_info:
            client.upload_file(
                file_path=temp_file,
                course_id=course_id,
                folder_id=folder_id
            )
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_delete_other_user_file(self, client: CampusLLMClient, logged_in_user,
                                  another_user, test_semester, temp_file):
        """删除其他用户的文件"""
        # 另一个用户创建课程、文件夹并上传文件
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        from .factories import create_test_course
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        course_id = self.extract_id_from_response(course_response, "course")
        
        folder_response = another_client.create_folder(course_id, 
                                                     name="其他用户文件夹", 
                                                     folder_type="lecture")
        folder_id = self.extract_id_from_response(folder_response, "folder")
        
        upload_response = another_client.upload_file(
            file_path=temp_file,
            course_id=course_id,
            folder_id=folder_id
        )
        file_id = self.extract_id_from_response(upload_response, "file")
        
        # 当前用户尝试删除其他用户的文件
        with pytest.raises(APIException) as exc_info:
            client.delete_file(file_id)
        
        self.assert_forbidden_response(exc_info.value)