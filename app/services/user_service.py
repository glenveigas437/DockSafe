from app.mappers.user_mapper import UserMapper
from app.models import User
from datetime import datetime, timezone, timedelta
from app.services.timezone_service import TimezoneService
from app.services.email_service import EmailService

class UserService:
    @staticmethod
    def authenticate_user(user_info):
        google_id = user_info.get('id')
        email = user_info.get('email')
        
        user = UserMapper.find_by_google_id(google_id)
        
        if not user:
            user = UserMapper.find_by_email(email)
            
            if user:
                user.google_id = google_id
                user.picture_url = user_info.get('picture')
                UserMapper.update_user(user.id, google_id=google_id, picture_url=user_info.get('picture'))
            else:
                user = UserMapper.create_user(
                    email=email,
                    google_id=google_id,
                    first_name=user_info.get('given_name'),
                    last_name=user_info.get('family_name'),
                    picture_url=user_info.get('picture')
                )
        
        # Update user with latest Google data and current time based on country
        current_time = datetime.now(timezone.utc)  # Default to UTC if no country set
        if user.country:
            current_time = TimezoneService.get_current_time_for_country(user.country)
        
        UserMapper.update_user(user.id, 
                              first_name=user_info.get('given_name'),
                              last_name=user_info.get('family_name'),
                              picture_url=user_info.get('picture'),
                              last_login=current_time)
        
        return user
    
    @staticmethod
    def update_user_profile(user_id, first_name=None, last_name=None, country=None):
        """Update user profile information"""
        user = UserMapper.find_by_id(user_id)
        if not user:
            return None
        
        update_data = {}
        if first_name is not None:
            update_data['first_name'] = first_name
        if last_name is not None:
            update_data['last_name'] = last_name
        if country is not None:
            update_data['country'] = country
            update_data['timezone'] = TimezoneService.get_timezone_for_country(country)
        
        UserMapper.update_user(user_id, **update_data)
        return UserMapper.find_by_id(user_id)
    
    @staticmethod
    def send_email_verification(user_id):
        """Send email verification to user"""
        user = UserMapper.find_by_id(user_id)
        if not user or user.email_verified:
            return False
        
        # Generate verification token
        verification_token = EmailService.generate_verification_token()
        
        # Update user with verification token
        UserMapper.update_user(user_id, email_verification_token=verification_token)
        
        # Send verification email
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email.split('@')[0]
        return EmailService.send_verification_email(user.email, verification_token, user_name)
    
    @staticmethod
    def verify_email(token):
        """Verify user email with token"""
        user = User.query.filter_by(email_verification_token=token).first()
        if not user:
            return False
        
        # Update user as verified and clear token
        UserMapper.update_user(user.id, email_verified=True, email_verification_token=None)
        
        # Send welcome email
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email.split('@')[0]
        EmailService.send_welcome_email(user.email, user_name)
        
        return True
    @staticmethod
    def get_user_by_id(user_id):
        return UserMapper.find_by_id(user_id)
    
    @staticmethod
    def get_user_groups(user_id):
        return UserMapper.get_user_groups(user_id)
    
    @staticmethod
    def update_user_last_login(user_id):
        # Use IST timezone (UTC+5:30)
        ist_timezone = timezone(timedelta(hours=5, minutes=30))
        UserMapper.update_user(user_id, last_login=datetime.now(ist_timezone))
