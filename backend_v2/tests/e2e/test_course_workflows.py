"""
课程管理相关的End-to-End工作流测试
"""
import pytest
from .base import AdminE2ETest, UserE2ETest
from .api_client import CampusLLMClient, APIException
from .factories import create_test_semester, create_test_course


@pytest.mark.course
@pytest.mark.admin
class TestSemesterManagementWorkflow(AdminE2ETest):
    """学期管理工作流测试（管理员权限）"""
    
    @pytest.mark.smoke
    def test_complete_semester_lifecycle(self, admin_client: CampusLLMClient):
        """完整的学期生命周期测试"""
        # 1. 创建学期
        semester_data = create_test_semester()
        create_response = admin_client.create_semester(**semester_data)
        
        self.assert_success_response(create_response)
        semester_id = self.extract_id_from_response(create_response, "semester")
        
        # 2. 获取学期列表
        list_response = admin_client.get_semesters()
        print(f"🔍 Debug - get_semesters response: {list_response}")
        self.assert_success_response(list_response)
        self.assert_semester_response(list_response)
        
        # 验证创建的学期在列表中
        semesters = list_response["data"]["semesters"]
        semester_ids = [s["id"] for s in semesters]
        assert semester_id in semester_ids
        
        # 3. 获取学期详情
        detail_response = admin_client.get_semester(semester_id)
        self.assert_success_response(detail_response)
        self.assert_semester_response(detail_response)
        
        semester_detail = detail_response["data"]["semester"]
        assert semester_detail["id"] == semester_id
        assert semester_detail["name"] == semester_data["name"]
        assert semester_detail["code"] == semester_data["code"]
        
        # 4. 更新学期
        update_data = {
            "name": "更新后的学期名称",
            "description": "更新后的描述"
        }
        update_response = admin_client.update_semester(semester_id, **update_data)
        self.assert_success_response(update_response)
        
        # 验证更新是否生效
        updated_detail = admin_client.get_semester(semester_id)
        updated_semester = updated_detail["data"]["semester"]
        assert updated_semester["name"] == update_data["name"]
        
        # 5. 获取学期课程（应该为空）
        courses_response = admin_client.get_semester_courses(semester_id)
        self.assert_success_response(courses_response)
        self.assert_course_response(courses_response)
        
        courses = courses_response["data"]["courses"]
        assert len(courses) == 0
        
        # 6. 删除学期（没有课程时应该成功）
        delete_response = admin_client.delete_semester(semester_id)
        self.assert_success_response(delete_response)
        
        # 验证删除是否生效
        with pytest.raises(APIException) as exc_info:
            admin_client.get_semester(semester_id)
        self.assert_not_found_response(exc_info.value)
    
    def test_create_semester_with_duplicate_code(self, admin_client: CampusLLMClient):
        """创建重复代码的学期"""
        semester_data = create_test_semester()
        
        # 创建第一个学期
        response1 = admin_client.create_semester(**semester_data)
        self.assert_success_response(response1)
        
        # 尝试创建相同代码的学期
        with pytest.raises(APIException) as exc_info:
            admin_client.create_semester(**semester_data)
        
        self.assert_conflict_response(exc_info.value)
    
    def test_update_semester_with_invalid_date_range(self, admin_client: CampusLLMClient):
        """使用无效日期范围更新学期"""
        semester_data = create_test_semester()
        create_response = admin_client.create_semester(**semester_data)
        semester_id = self.extract_id_from_response(create_response, "semester")
        
        # 结束日期早于开始日期
        invalid_update = {
            "start_date": "2024-06-01",
            "end_date": "2024-02-01"
        }
        
        with pytest.raises(APIException) as exc_info:
            admin_client.update_semester(semester_id, **invalid_update)
        
        assert exc_info.value.status_code in [400, 422]
    
    def test_delete_semester_with_courses(self, admin_client: CampusLLMClient, 
                                        client: CampusLLMClient, logged_in_user):
        """删除有课程的学期（应该失败）"""
        # 创建学期
        semester_data = create_test_semester()
        semester_response = admin_client.create_semester(**semester_data)
        semester_id = self.extract_id_from_response(semester_response, "semester")
        
        # 创建课程
        course_data = create_test_course(semester_id)
        course_response = client.create_course(**course_data)
        self.assert_success_response(course_response)
        
        # 尝试删除有课程的学期
        with pytest.raises(APIException) as exc_info:
            admin_client.delete_semester(semester_id)
        
        self.assert_conflict_response(exc_info.value)


@pytest.mark.course
class TestCourseManagementWorkflow(UserE2ETest):
    """课程管理工作流测试（用户权限）"""
    
    @pytest.mark.smoke
    def test_complete_course_lifecycle(self, client: CampusLLMClient, logged_in_user,
                                     test_semester):
        """完整的课程生命周期测试"""
        semester_id = test_semester["semester"]["id"]
        
        # 1. 创建课程
        course_data = create_test_course(semester_id)
        create_response = client.create_course(**course_data)
        
        self.assert_success_response(create_response)
        course_id = self.extract_id_from_response(create_response, "course")
        
        # 2. 获取课程列表
        list_response = client.get_courses()
        self.assert_success_response(list_response)
        self.assert_course_response(list_response)
        
        # 验证创建的课程在列表中
        courses = list_response["data"]["courses"]
        course_ids = [c["id"] for c in courses]
        assert course_id in course_ids
        
        # 3. 按学期过滤课程
        filtered_response = client.get_courses(semester_id=semester_id)
        self.assert_success_response(filtered_response)
        filtered_courses = filtered_response["data"]["courses"]
        
        # 所有课程都应该属于指定学期
        for course in filtered_courses:
            assert course["semester_id"] == semester_id
        
        # 4. 获取课程详情
        detail_response = client.get_course(course_id)
        self.assert_success_response(detail_response)
        self.assert_course_response(detail_response)
        
        course_detail = detail_response["data"]["course"]
        assert course_detail["id"] == course_id
        assert course_detail["name"] == course_data["name"]
        assert course_detail["code"] == course_data["code"]
        assert course_detail["semester_id"] == semester_id
        
        # 5. 更新课程
        update_data = {
            "name": "更新后的课程名称",
            "description": "更新后的课程描述"
        }
        update_response = client.update_course(course_id, **update_data)
        self.assert_success_response(update_response)
        
        # 验证更新是否生效
        updated_detail = client.get_course(course_id)
        updated_course = updated_detail["data"]["course"]
        assert updated_course["name"] == update_data["name"]
        
        # 6. 删除课程
        delete_response = client.delete_course(course_id)
        self.assert_success_response(delete_response)
        
        # 验证删除是否生效
        with pytest.raises(APIException) as exc_info:
            client.get_course(course_id)
        self.assert_not_found_response(exc_info.value)
    
    def test_create_course_with_duplicate_code_same_semester(self, client: CampusLLMClient, 
                                                           logged_in_user, test_semester):
        """在同一学期创建重复代码的课程"""
        semester_id = test_semester["semester"]["id"]
        course_data = create_test_course(semester_id)
        
        # 创建第一个课程
        response1 = client.create_course(**course_data)
        self.assert_success_response(response1)
        
        # 尝试在同一学期创建相同代码的课程
        with pytest.raises(APIException) as exc_info:
            client.create_course(**course_data)
        
        self.assert_conflict_response(exc_info.value)
    
    def test_create_course_with_same_code_different_semester(self, client: CampusLLMClient,
                                                           logged_in_user, admin_client: CampusLLMClient):
        """在不同学期创建相同代码的课程（应该允许）"""
        # 创建两个学期
        semester1_data = create_test_semester()
        semester1_response = admin_client.create_semester(**semester1_data)
        semester1_id = self.extract_id_from_response(semester1_response, "semester")
        
        semester2_data = create_test_semester()
        semester2_data["code"] = semester1_data["code"] + "2"  # 确保学期代码不重复
        semester2_response = admin_client.create_semester(**semester2_data)
        semester2_id = self.extract_id_from_response(semester2_response, "semester")
        
        # 在第一个学期创建课程
        course_data = create_test_course(semester1_id)
        response1 = client.create_course(**course_data)
        self.assert_success_response(response1)
        
        # 在第二个学期创建相同代码的课程（应该成功）
        course_data2 = course_data.copy()
        course_data2["semester_id"] = semester2_id
        response2 = client.create_course(**course_data2)
        self.assert_success_response(response2)
    
    def test_create_course_with_inactive_semester(self, client: CampusLLMClient, 
                                                logged_in_user, admin_client: CampusLLMClient):
        """在非活跃学期创建课程"""
        # 创建学期
        semester_data = create_test_semester()
        semester_response = admin_client.create_semester(**semester_data)
        semester_id = self.extract_id_from_response(semester_response, "semester")
        
        # 停用学期
        admin_client.update_semester(semester_id, is_active=False)
        
        # 尝试在停用的学期创建课程
        course_data = create_test_course(semester_id)
        
        with pytest.raises(APIException) as exc_info:
            client.create_course(**course_data)
        
        assert exc_info.value.status_code in [400, 404]
    
    def test_access_other_user_course(self, client: CampusLLMClient, another_user, 
                                    test_semester):
        """访问其他用户的课程（权限测试）"""
        # 另一个用户创建课程
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        course_id = self.extract_id_from_response(course_response, "course")
        
        # 当前用户尝试访问其他用户的课程
        with pytest.raises(APIException) as exc_info:
            client.get_course(course_id)
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_update_other_user_course(self, client: CampusLLMClient, another_user, 
                                    test_semester):
        """更新其他用户的课程（权限测试）"""
        # 另一个用户创建课程
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        course_id = self.extract_id_from_response(course_response, "course")
        
        # 当前用户尝试更新其他用户的课程
        with pytest.raises(APIException) as exc_info:
            client.update_course(course_id, name="恶意更新")
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_delete_other_user_course(self, client: CampusLLMClient, another_user, 
                                    test_semester):
        """删除其他用户的课程（权限测试）"""
        # 另一个用户创建课程
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        course_data = create_test_course(test_semester["semester"]["id"])
        course_response = another_client.create_course(**course_data)
        course_id = self.extract_id_from_response(course_response, "course")
        
        # 当前用户尝试删除其他用户的课程
        with pytest.raises(APIException) as exc_info:
            client.delete_course(course_id)
        
        self.assert_forbidden_response(exc_info.value)


@pytest.mark.course
class TestCourseDataIsolation(UserE2ETest):
    """课程数据隔离测试"""
    
    def test_user_course_list_isolation(self, client: CampusLLMClient, logged_in_user,
                                      another_user, test_semester):
        """用户课程列表隔离测试"""
        semester_id = test_semester["semester"]["id"]
        
        # 当前用户创建课程
        course_data1 = create_test_course(semester_id)
        client.create_course(**course_data1)
        
        # 另一个用户创建课程
        another_client = CampusLLMClient(base_url=client.base_url)
        another_client.login(
            another_user["user_data"]["username"], 
            another_user["user_data"]["password"]
        )
        
        course_data2 = create_test_course(semester_id)
        course_data2["code"] = course_data1["code"] + "2"  # 确保代码不重复
        another_client.create_course(**course_data2)
        
        # 验证当前用户只能看到自己的课程
        user1_courses = client.get_courses()
        courses1 = user1_courses["data"]["courses"]
        course1_names = [c["name"] for c in courses1]
        
        assert course_data1["name"] in course1_names
        assert course_data2["name"] not in course1_names
        
        # 验证另一个用户只能看到自己的课程
        user2_courses = another_client.get_courses()
        courses2 = user2_courses["data"]["courses"]
        course2_names = [c["name"] for c in courses2]
        
        assert course_data2["name"] in course2_names
        assert course_data1["name"] not in course2_names


@pytest.mark.course
@pytest.mark.admin
class TestSemesterPermissions(AdminE2ETest):
    """学期权限测试"""
    
    def test_regular_user_cannot_create_semester(self, client: CampusLLMClient, 
                                               logged_in_user):
        """普通用户不能创建学期"""
        semester_data = create_test_semester()
        
        with pytest.raises(APIException) as exc_info:
            client.create_semester(**semester_data)
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_regular_user_cannot_update_semester(self, client: CampusLLMClient, 
                                               logged_in_user, test_semester):
        """普通用户不能更新学期"""
        semester_id = test_semester["semester"]["id"]
        
        with pytest.raises(APIException) as exc_info:
            client.update_semester(semester_id, name="恶意更新")
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_regular_user_cannot_delete_semester(self, client: CampusLLMClient, 
                                               logged_in_user, test_semester):
        """普通用户不能删除学期"""
        semester_id = test_semester["semester"]["id"]
        
        with pytest.raises(APIException) as exc_info:
            client.delete_semester(semester_id)
        
        self.assert_forbidden_response(exc_info.value)
    
    def test_regular_user_can_read_semesters(self, client: CampusLLMClient, 
                                           logged_in_user, test_semester):
        """普通用户可以读取学期信息"""
        # 获取学期列表
        list_response = client.get_semesters()
        print(f"🔍 Debug - user get_semesters response: {list_response}")
        self.assert_success_response(list_response)
        self.assert_semester_response(list_response)
        
        # 获取学期详情
        semester_id = test_semester["semester"]["id"]
        detail_response = client.get_semester(semester_id)
        self.assert_success_response(detail_response)
        self.assert_semester_response(detail_response)
        
        # 获取学期课程
        courses_response = client.get_semester_courses(semester_id)
        self.assert_success_response(courses_response)
        self.assert_course_response(courses_response)