from app.models import User
from app import db
from datetime import datetime


class UserMapper:
    @staticmethod
    def find_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def find_by_google_id(google_id):
        return User.query.filter_by(google_id=google_id).first()

    @staticmethod
    def create_user(
        email, google_id=None, first_name=None, last_name=None, picture_url=None
    ):
        user = User(
            email=email,
            google_id=google_id,
            first_name=first_name,
            last_name=last_name,
            picture_url=picture_url,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.session.commit()

    @staticmethod
    def get_user_groups(user_id):
        user = User.query.get(user_id)
        return list(user.groups) if user else []
