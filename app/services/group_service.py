from app.mappers.group_mapper import GroupMapper
from app.models import Group
from app.constants import DatabaseConstants

class GroupService:
    @staticmethod
    def create_group(name, description, created_by):
        return GroupMapper.create_group(name, description, created_by)
    
    @staticmethod
    def get_group_by_id(group_id):
        return GroupMapper.find_by_id(group_id)
    
    @staticmethod
    def get_user_groups(user_id):
        return GroupMapper.get_user_groups(user_id)
    
    @staticmethod
    def add_member_to_group(group_id, user_id, role=DatabaseConstants.DEFAULT_ROLE):
        return GroupMapper.add_member(group_id, user_id, role)
    
    @staticmethod
    def remove_member_from_group(group_id, user_id):
        return GroupMapper.remove_member(group_id, user_id)
    
    @staticmethod
    def get_user_role_in_group(group_id, user_id):
        return GroupMapper.get_user_role(group_id, user_id)
    
    @staticmethod
    def is_user_member_of_group(group_id, user_id):
        return GroupMapper.is_member(group_id, user_id)
    
    @staticmethod
    def check_admin_permission(user_id):
        groups = GroupMapper.get_user_groups(user_id)
        for group in groups:
            role = GroupMapper.get_user_role(group.id, user_id)
            if role and role in DatabaseConstants.USER_ROLES[1:]:
                return True
        return False
