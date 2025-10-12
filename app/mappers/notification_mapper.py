from app.models import NotificationConfiguration, NotificationHistory
from app import db


class NotificationMapper:
    @staticmethod
    def create_configuration(
        name,
        type,
        service,
        group_id,
        webhook_url=None,
        channel=None,
        subject_template=None,
        notify_critical=True,
        notify_high=True,
        notify_medium=False,
        notify_low=False,
        notify_scan_failed=True,
        notify_daily_summary=False,
        additional_config=None,
    ):
        config = NotificationConfiguration(
            name=name,
            type=type,
            service=service,
            group_id=group_id,
            webhook_url=webhook_url,
            channel=channel,
            subject_template=subject_template,
            notify_critical=notify_critical,
            notify_high=notify_high,
            notify_medium=notify_medium,
            notify_low=notify_low,
            notify_scan_failed=notify_scan_failed,
            notify_daily_summary=notify_daily_summary,
            additional_config=additional_config,
        )
        db.session.add(config)
        db.session.commit()

    @staticmethod
    def get_configurations_by_group(group_id):
        return NotificationConfiguration.query.filter_by(
            group_id=group_id, is_active=True
        ).all()

    @staticmethod
    def get_configuration_by_type_service(type, service, group_id):
        return NotificationConfiguration.query.filter_by(
            type=type, service=service, group_id=group_id
        ).first()

    @staticmethod
    def update_configuration(config_id, **kwargs):
        config = NotificationConfiguration.query.get(config_id)
        if config:
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            db.session.commit()

    @staticmethod
    def delete_configuration(config_id):
        config = NotificationConfiguration.query.get(config_id)
        if config:
            db.session.delete(config)
            db.session.commit()

    @staticmethod
    def create_notification_history(
        scan_id,
        group_id,
        notification_type,
        recipient,
        message_content,
        status="SENT",
        error_message=None,
        notification_metadata=None,
    ):
        history = NotificationHistory(
            scan_id=scan_id,
            group_id=group_id,
            notification_type=notification_type,
            recipient=recipient,
            message_content=message_content,
            status=status,
            error_message=error_message,
            notification_metadata=notification_metadata,
        )
        db.session.add(history)
        db.session.commit()

    @staticmethod
    def get_notification_history(group_id, limit=50):
        return (
            NotificationHistory.query.filter_by(group_id=group_id)
            .order_by(NotificationHistory.sent_at.desc())
            .limit(limit)
            .all()
        )
