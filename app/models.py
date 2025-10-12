from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON
from flask_login import UserMixin

user_groups = db.Table(
    "user_groups",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("groups.id"), primary_key=True),
    db.Column("joined_at", db.DateTime, default=datetime.utcnow),
    db.Column("role", db.String(20), default="member"),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=True)
    google_id = db.Column(db.String(120), unique=True, nullable=True, index=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    picture_url = db.Column(db.String(500), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "picture_url": self.picture_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    @property
    def groups(self):
        return (
            db.session.query(Group)
            .join(user_groups)
            .filter(user_groups.c.user_id == self.id)
            .all()
        )

    def is_member_of_group(self, group_id):
        return (
            db.session.query(user_groups)
            .filter(
                user_groups.c.user_id == self.id, user_groups.c.group_id == group_id
            )
            .first()
            is not None
        )

    def get_role_in_group(self, group_id):
        result = db.session.execute(
            db.select(user_groups.c.role).where(
                db.and_(
                    user_groups.c.user_id == self.id, user_groups.c.group_id == group_id
                )
            )
        ).scalar()
        return result or "member"


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Group {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }

    @property
    def members(self):
        return (
            db.session.query(User)
            .join(user_groups)
            .filter(user_groups.c.group_id == self.id)
            .all()
        )

    @property
    def vulnerability_scans(self):
        return VulnerabilityScan.query.filter_by(group_id=self.id)

    def is_member(self, user):
        return (
            db.session.query(user_groups)
            .filter(user_groups.c.user_id == user.id, user_groups.c.group_id == self.id)
            .first()
            is not None
        )

    def get_user_role(self, user):
        result = db.session.execute(
            db.select(user_groups.c.role).where(
                db.and_(
                    user_groups.c.user_id == user.id, user_groups.c.group_id == self.id
                )
            )
        ).scalar()
        return result or "member"

    def add_member(self, user, role="member"):
        if not self.is_member(user):
            db.session.execute(
                user_groups.insert().values(
                    user_id=user.id, group_id=self.id, role=role
                )
            )
            db.session.commit()

    def remove_member(self, user):
        db.session.execute(
            user_groups.delete().where(
                db.and_(
                    user_groups.c.user_id == user.id, user_groups.c.group_id == self.id
                )
            )
        )
        db.session.commit()

    @staticmethod
    def find_by_name(name):
        return Group.query.filter_by(name=name).first()


class VulnerabilityScan(db.Model):
    """Model for vulnerability scan results"""

    __tablename__ = "vulnerability_scans"

    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(255), nullable=False, index=True)
    image_tag = db.Column(db.String(100), nullable=False)
    scan_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    scan_status = db.Column(
        db.String(50), nullable=False
    )  # SUCCESS, FAILED, IN_PROGRESS
    total_vulnerabilities = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    high_count = db.Column(db.Integer, default=0)
    medium_count = db.Column(db.Integer, default=0)
    low_count = db.Column(db.Integer, default=0)
    scan_duration_seconds = db.Column(db.Integer)
    scanner_version = db.Column(db.String(50))
    scanner_type = db.Column(db.String(20), default="trivy")  # trivy, clair
    scan_output = db.Column(db.Text)  # Raw scanner output
    scan_metadata = db.Column(JSON)  # Additional scan metadata
    group_id = db.Column(
        db.Integer, db.ForeignKey("groups.id"), nullable=False, index=True
    )
    creator_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    vulnerabilities = db.relationship(
        "Vulnerability", backref="scan", lazy="dynamic", cascade="all, delete-orphan"
    )
    notifications = db.relationship("NotificationHistory", lazy="dynamic")
    group = db.relationship("Group", backref="scans")
    creator = db.relationship("User", backref="created_scans")

    def __repr__(self):
        return f"<VulnerabilityScan {self.image_name}:{self.image_tag} - {self.scan_status}>"

    @property
    def has_critical_vulnerabilities(self):
        """Check if scan has critical vulnerabilities"""
        return self.critical_count > 0

    @property
    def has_high_vulnerabilities(self):
        """Check if scan has high severity vulnerabilities"""
        return self.high_count > 0

    @property
    def severity_summary(self):
        """Get vulnerability severity summary"""
        return {
            "critical": self.critical_count,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "total": self.total_vulnerabilities,
        }

    def to_dict(self):
        """Convert scan to dictionary"""
        return {
            "id": self.id,
            "image_name": self.image_name,
            "image_tag": self.image_tag,
            "scan_timestamp": self.scan_timestamp.isoformat()
            if self.scan_timestamp
            else None,
            "scan_status": self.scan_status,
            "total_vulnerabilities": self.total_vulnerabilities,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "scan_duration_seconds": self.scan_duration_seconds,
            "scanner_version": self.scanner_version,
            "scanner_type": self.scanner_type,
            "scan_metadata": self.scan_metadata,
            "group_id": self.group_id,
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Vulnerability(db.Model):
    """Model for individual vulnerabilities"""

    __tablename__ = "vulnerabilities"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(
        db.Integer, db.ForeignKey("vulnerability_scans.id"), nullable=False
    )
    cve_id = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(
        db.String(20), nullable=False, index=True
    )  # CRITICAL, HIGH, MEDIUM, LOW
    package_name = db.Column(db.String(255), nullable=False, index=True)
    package_version = db.Column(db.String(100))
    fixed_version = db.Column(db.String(100))
    description = db.Column(db.Text)
    cvss_score = db.Column(db.Numeric(3, 1))
    cvss_vector = db.Column(db.String(100))
    published_date = db.Column(db.DateTime)
    last_modified_date = db.Column(db.DateTime)
    references = db.Column(JSON)  # List of reference URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vulnerability {self.cve_id} - {self.severity}>"

    def to_dict(self):
        """Convert vulnerability to dictionary"""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "cve_id": self.cve_id,
            "severity": self.severity,
            "package_name": self.package_name,
            "package_version": self.package_version,
            "fixed_version": self.fixed_version,
            "description": self.description,
            "cvss_score": float(self.cvss_score) if self.cvss_score else None,
            "cvss_vector": self.cvss_vector,
            "published_date": self.published_date.isoformat()
            if self.published_date
            else None,
            "last_modified_date": self.last_modified_date.isoformat()
            if self.last_modified_date
            else None,
            "references": self.references,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ScanException(db.Model):
    """Model for scan exceptions (approved vulnerabilities)"""

    __tablename__ = "scan_exceptions"

    id = db.Column(db.Integer, primary_key=True)
    cve_id = db.Column(db.String(50), nullable=False, index=True)
    image_name = db.Column(
        db.String(255), nullable=True, index=True
    )  # Null for global exceptions
    reason = db.Column(db.Text, nullable=False)
    approved_by = db.Column(db.String(100), nullable=False)
    approved_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Null for permanent exceptions
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<ScanException {self.cve_id} - {self.approved_by}>"

    @property
    def is_expired(self):
        """Check if exception has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if exception is valid (active and not expired)"""
        return self.is_active and not self.is_expired

    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            "id": self.id,
            "cve_id": self.cve_id,
            "image_name": self.image_name,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationConfiguration(db.Model):
    """Model for notification configuration settings"""

    __tablename__ = "notification_configurations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # chat, email, webhook
    service = db.Column(db.String(50), nullable=False)  # Slack, Teams, Gmail, etc.
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    webhook_url = db.Column(db.String(500), nullable=True)
    channel = db.Column(db.String(100), nullable=True)
    email_recipients = db.Column(db.Text, nullable=True)  # JSON array of emails
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    group = db.relationship("Group", backref="notification_configurations")

    def __repr__(self):
        return f"<NotificationConfiguration {self.name} - {self.service}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "service": self.service,
            "group_id": self.group_id,
            "webhook_url": self.webhook_url,
            "channel": self.channel,
            "email_recipients": self.email_recipients,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationHistory(db.Model):
    """Model for notification history"""

    __tablename__ = "notification_history"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(
        db.Integer, db.ForeignKey("vulnerability_scans.id"), nullable=True
    )
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    notification_type = db.Column(
        db.String(50), nullable=False
    )  # SLACK, TEAMS, EMAIL, WEBHOOK
    recipient = db.Column(db.String(255), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="SENT")  # SENT, FAILED, PENDING
    error_message = db.Column(db.Text)
    notification_metadata = db.Column(JSON)  # Additional notification metadata

    # Relationships
    vulnerability_scan = db.relationship("VulnerabilityScan", lazy="select")
    group = db.relationship("Group", backref="notification_history")

    def __repr__(self):
        return f"<NotificationHistory {self.notification_type} - {self.status}>"

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "notification_type": self.notification_type,
            "recipient": self.recipient,
            "message_content": self.message_content,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "error_message": self.error_message,
            "notification_metadata": self.notification_metadata,
        }


class ScanConfiguration(db.Model):
    """Model for scan configuration settings"""

    __tablename__ = "scan_configurations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    scanner_type = db.Column(db.String(20), default="trivy")  # trivy, clair
    vulnerability_threshold = db.Column(
        db.String(20), default="HIGH"
    )  # CRITICAL, HIGH, MEDIUM, LOW
    scan_timeout = db.Column(db.Integer, default=300)  # seconds
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<ScanConfiguration {self.name}>"

    def to_dict(self):
        """Convert configuration to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scanner_type": self.scanner_type,
            "vulnerability_threshold": self.vulnerability_threshold,
            "scan_timeout": self.scan_timeout,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
