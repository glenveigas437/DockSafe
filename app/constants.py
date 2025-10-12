class DatabaseConstants:
    USER_ROLES = ['member', 'admin', 'owner']
    DEFAULT_ROLE = 'member'
    
    SCAN_STATUSES = ['SUCCESS', 'FAILED', 'IN_PROGRESS']
    SCANNER_TYPES = ['trivy', 'clair']
    DEFAULT_SCANNER_TYPE = 'trivy'
    
    VULNERABILITY_SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    DEFAULT_VULNERABILITY_THRESHOLD = 'HIGH'
    
    NOTIFICATION_TYPES = ['SLACK', 'TEAMS', 'EMAIL', 'WEBHOOK']
    NOTIFICATION_SERVICES = ['Slack', 'Teams', 'Gmail']
    NOTIFICATION_STATUSES = ['SENT', 'FAILED', 'PENDING']
    
    DEFAULT_SCAN_TIMEOUT = 300
    DEFAULT_EMAIL_SMTP_PORT = 587
    DEFAULT_EMAIL_SMTP_SERVER = 'smtp.gmail.com'

class ValidationConstants:
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    IMAGE_NAME_PATTERN = r'^[a-zA-Z0-9._/-]+$'
    IMAGE_TAG_PATTERN = r'^[a-zA-Z0-9._-]+$'
    
    MAX_USERNAME_LENGTH = 80
    MAX_EMAIL_LENGTH = 120
    MAX_GROUP_NAME_LENGTH = 100
    MAX_IMAGE_NAME_LENGTH = 255
    MAX_IMAGE_TAG_LENGTH = 100
    MAX_CVE_ID_LENGTH = 50
    MAX_PACKAGE_NAME_LENGTH = 255
    MAX_PACKAGE_VERSION_LENGTH = 100
    MAX_PICTURE_URL_LENGTH = 500

class SeverityConstants:
    SEVERITY_LEVELS = {
        'CRITICAL': 4,
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1
    }
    
    SEVERITY_COLORS = {
        'CRITICAL': 'red',
        'HIGH': 'orange',
        'MEDIUM': 'yellow',
        'LOW': 'green'
    }

class NotificationConstants:
    DEFAULT_EMAIL_SUBJECT_PREFIX = '[DockSafe]'
    DEFAULT_NOTIFICATION_SETTINGS = {
        'notify_critical': True,
        'notify_high': True,
        'notify_medium': False,
        'notify_low': False,
        'notify_scan_failed': True,
        'notify_daily_summary': False
    }

class SystemConstants:
    DEFAULT_CHART_DAYS = 7
    DEFAULT_STATISTICS_DAYS = 30
    DEFAULT_SCAN_LIMIT = 50
    DEFAULT_RECENT_SCANS_LIMIT = 5
    DEFAULT_NOTIFICATION_HISTORY_LIMIT = 50
    
    SYSTEM_STATUS = {
        'scanner_service': 'Online',
        'database': 'Connected',
        'api_gateway': 'Operational',
        'notification_service': 'Operational'
    }

class ErrorMessages:
    USER_NOT_FOUND = 'User not found'
    GROUP_NOT_FOUND = 'Group not found'
    SCAN_NOT_FOUND = 'Scan not found'
    CONFIGURATION_NOT_FOUND = 'Configuration not found'
    NO_GROUP_SELECTED = 'No group selected'
    ADMIN_PRIVILEGES_REQUIRED = 'Admin privileges required'
    INSUFFICIENT_PERMISSIONS = 'Insufficient permissions'
    VALIDATION_FAILED = 'Validation failed'
    DATABASE_OPERATION_FAILED = 'Database operation failed'
    GOOGLE_OAUTH_NOT_CONFIGURED = 'Google OAuth is not configured. Please contact your administrator.'
    GOOGLE_OAUTH_NOT_AVAILABLE = 'Google OAuth is not available. Please contact your administrator.'
    EMAIL_NOT_VERIFIED = 'Email address not verified by Google. Please verify your email and try again.'
    ACCOUNT_DEACTIVATED = 'Your account has been deactivated. Please contact your administrator.'
    AUTHORIZATION_FAILED = 'Authorization failed. Please try again.'
    INVALID_STATE_PARAMETER = 'Invalid state parameter. Please try again.'
    AUTHENTICATION_FAILED = 'Authentication failed. Please try again.'
    IMAGE_NOT_FOUND = 'Image not found. Please check if the image exists and is accessible.'
    IMAGE_NOT_FOUND_RUNTIME = 'Image not found in any container runtime. Please ensure the image exists locally or is available on Docker Hub.'
    SCAN_FAILED = 'Scan failed'
    TEAMS_NOT_IMPLEMENTED = 'Teams integration not yet implemented'
    EMAIL_NOT_IMPLEMENTED = 'Email integration not yet implemented'
    INVALID_WEBHOOK_URL = 'Invalid webhook URL'
    TEST_MESSAGE_SENT = 'Test message sent successfully'
    TEST_MESSAGE_FAILED = 'Failed to send test message'

class SuccessMessages:
    SUCCESS = 'Success'
    LOGGED_OUT_SUCCESSFULLY = 'Logged out successfully'
    SETTINGS_SAVED_SUCCESSFULLY = 'Settings saved successfully'
    CONFIGURATION_CREATED_SUCCESSFULLY = 'Configuration created successfully'
    CONFIGURATION_UPDATED_SUCCESSFULLY = 'Configuration updated successfully'
    CONFIGURATION_DELETED_SUCCESSFULLY = 'Configuration deleted successfully'
    NOTIFICATION_CONFIGURATIONS_REFRESHED = 'Notification configurations refreshed successfully'
    TEST_NOTIFICATIONS_COMPLETED = 'Test notifications completed'

class APIEndpoints:
    SCANNER = '/scanner'
    REPORTS = '/reports'
    NOTIFICATIONS = '/notifications'
    DASHBOARD = '/dashboard'

class SessionKeys:
    USER_ID = 'user_id'
    USERNAME = 'username'
    EMAIL = 'email'
    PICTURE_URL = 'picture_url'
    ACCESS_TOKEN = 'access_token'
    SELECTED_GROUP_ID = 'selected_group_id'
    OAUTH_STATE = 'oauth_state'

class HTTPStatusCodes:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500

class ResponseKeys:
    SUCCESS = 'success'
    ERROR = 'error'
    MESSAGE = 'message'
    DATA = 'data'
    ERROR_CODE = 'error_code'
    USER = 'user'
    CONFIGURATION = 'configuration'
    CONFIGURATIONS = 'configurations'
    NOTIFICATIONS = 'notifications'
    RESULTS = 'results'
