from app.models import Group, user_groups
from app.constants import DatabaseConstants
from app import db


class GroupMapper:
    @staticmethod
    def find_by_id(group_id):
        return Group.query.get(group_id)

    @staticmethod
    def find_by_name(name):
        return Group.query.filter_by(name=name).first()

    @staticmethod
    def get_user_groups(user_id):
        return (
            Group.query.join(user_groups).filter(user_groups.c.user_id == user_id).all()
        )

    @staticmethod
    def create_group(name, description, created_by):
        group = Group(name=name, description=description, created_by=created_by)
        db.session.add(group)
        db.session.commit()

    @staticmethod
    def add_member(group_id, user_id, role=DatabaseConstants.DEFAULT_ROLE):
        db.session.execute(
            user_groups.insert().values(user_id=user_id, group_id=group_id, role=role)
        )
        db.session.commit()

    @staticmethod
    def remove_member(group_id, user_id):
        db.session.execute(
            user_groups.delete().where(
                db.and_(
                    user_groups.c.user_id == user_id, user_groups.c.group_id == group_id
                )
            )
        )
        db.session.commit()

    @staticmethod
    def get_user_role(group_id, user_id):
        result = db.session.execute(
            db.select(user_groups.c.role).where(
                db.and_(
                    user_groups.c.user_id == user_id, user_groups.c.group_id == group_id
                )
            )
        ).scalar()

    @staticmethod
    def is_member(group_id, user_id):
        result = db.session.execute(
            db.select(user_groups.c.user_id).where(
                db.and_(
                    user_groups.c.user_id == user_id, user_groups.c.group_id == group_id
                )
            )
        ).scalar()
