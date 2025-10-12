from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.constants import ValidationConstants, SeverityConstants, DatabaseConstants, \
    SystemConstants, ErrorMessages, SuccessMessages, ResponseKeys, HTTPStatusCodes

class ValidationUtils:
    @staticmethod
    def is_valid_email(email: str) -> bool:
        return re.match(ValidationConstants.EMAIL_PATTERN, email) is not None
    
    @staticmethod
    def is_valid_image_name(image_name: str) -> bool:
        return re.match(ValidationConstants.IMAGE_NAME_PATTERN, image_name) is not None
    
    @staticmethod
    def is_valid_image_tag(image_tag: str) -> bool:
        return re.match(ValidationConstants.IMAGE_TAG_PATTERN, image_tag) is not None
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        return input_str.strip() if input_str else ""

class PasswordUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class DateTimeUtils:
    @staticmethod
    def get_current_utc() -> datetime:
        return datetime.utcnow()
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        return dt.isoformat() if dt else None
    
    @staticmethod
    def get_date_range(days: int) -> tuple:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    @staticmethod
    def is_expired(expires_at: Optional[datetime]) -> bool:
        if expires_at is None:
            return datetime.utcnow() > expires_at

class SeverityUtils:
    @staticmethod
    def get_severity_level(severity: str) -> int:
        return SeverityConstants.SEVERITY_LEVELS.get(severity.upper(), 0)
    
    @staticmethod
    def should_fail_build(critical_count: int, high_count: int, 
                         medium_count: int, low_count: int, 
                         threshold: str = DatabaseConstants.DEFAULT_VULNERABILITY_THRESHOLD) -> bool:
        threshold_level = SeverityUtils.get_severity_level(threshold)
        
        if threshold_level >= 4 and critical_count > 0:
            return True
        elif threshold_level >= 3 and high_count > 0:
            return True
        elif threshold_level >= 2 and medium_count > 0:
            return True
        elif threshold_level >= 1 and low_count > 0:
            return True
        
        return False
    @staticmethod
    def get_severity_color(severity: str) -> str:
        return SeverityConstants.SEVERITY_COLORS.get(severity.upper(), 'gray')

class ResponseUtils:
    @staticmethod
    def success_response(data: Any = None, message: str = SuccessMessages.SUCCESS) -> Dict[str, Any]:
        response = {ResponseKeys.SUCCESS: True, ResponseKeys.MESSAGE: message}
        if data is not None:
            response[ResponseKeys.DATA] = data
    
    @staticmethod
    def error_response(message: str, error_code: int = HTTPStatusCodes.BAD_REQUEST) -> Dict[str, Any]:
        return {ResponseKeys.SUCCESS: False, ResponseKeys.ERROR: message, ResponseKeys.ERROR_CODE: error_code}
    
    @staticmethod
    def format_scan_data(scan) -> Dict[str, Any]:
        return {
            'id': scan.id,
            'image_name': scan.image_name,
            'image_tag': scan.image_tag,
            'scan_timestamp': DateTimeUtils.format_datetime(scan.scan_timestamp),
            'scan_status': scan.scan_status,
            'total_vulnerabilities': scan.total_vulnerabilities,
            'critical_count': scan.critical_count,
            'high_count': scan.high_count,
            'medium_count': scan.medium_count,
            'low_count': scan.low_count,
            'scan_duration_seconds': scan.scan_duration_seconds,
            'scanner_type': scan.scanner_type,
            'scanner_version': scan.scanner_version
        }
