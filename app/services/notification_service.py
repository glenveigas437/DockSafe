import logging
from app.mappers.notification_mapper import NotificationMapper

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def get_notification_settings(group_id):
        configs = NotificationMapper.get_configurations_by_group(group_id)
        
        settings_data = {
            'slack_webhook': '',
            'slack_channel': '',
            'teams_webhook': '',
            'teams_channel': '',
            'email_recipients': '',
            'email_subject': '[DockSafe]',
            'email_smtp_server': 'smtp.gmail.com',
            'email_smtp_port': 587,
            'email_username': '',
            'email_password': '',
            'notify_critical': True,
            'notify_high': True,
            'notify_medium': False,
            'notify_low': False,
            'notify_scan_failed': True,
            'notify_daily_summary': False
        }
        
        for config in configs:
            if config.type == 'chat' and config.service == 'Slack':
                settings_data['slack_webhook'] = config.webhook_url or ''
                settings_data['slack_channel'] = config.channel or ''
                settings_data['notify_critical'] = config.notify_critical
                settings_data['notify_high'] = config.notify_high
                settings_data['notify_medium'] = config.notify_medium
                settings_data['notify_low'] = config.notify_low
                settings_data['notify_scan_failed'] = config.notify_scan_failed
                settings_data['notify_daily_summary'] = config.notify_daily_summary
            elif config.type == 'chat' and config.service == 'Teams':
                settings_data['teams_webhook'] = config.webhook_url or ''
                settings_data['teams_channel'] = config.channel or ''
            elif config.type == 'email' and config.service == 'Gmail':
                settings_data['email_recipients'] = config.channel or ''
                settings_data['email_subject'] = config.subject_template or '[DockSafe]'
                if config.additional_config:
                    settings_data['email_smtp_server'] = config.additional_config.get('smtp_server', 'smtp.gmail.com')
                    settings_data['email_smtp_port'] = config.additional_config.get('smtp_port', 587)
                    settings_data['email_username'] = config.additional_config.get('username', '')
                    settings_data['email_password'] = config.additional_config.get('password', '')
        
        return settings_data
    
    @staticmethod
    def save_notification_settings(group_id, data):
        if data.get('slack_webhook'):
            existing_slack = NotificationMapper.get_configuration_by_type_service('chat', 'Slack', group_id)
            
            if existing_slack:
                NotificationMapper.update_configuration(existing_slack.id,
                                                       webhook_url=data.get('slack_webhook'),
                                                       channel=data.get('slack_channel'),
                                                       notify_critical=data.get('notify_critical', True),
                                                       notify_high=data.get('notify_high', True),
                                                       notify_medium=data.get('notify_medium', False),
                                                       notify_low=data.get('notify_low', False),
                                                       notify_scan_failed=data.get('notify_scan_failed', True),
                                                       notify_daily_summary=data.get('notify_daily_summary', False))
                NotificationMapper.create_configuration(
                    name='Slack Notifications',
                    type='chat',
                    service='Slack',
                    group_id=group_id,
                    webhook_url=data.get('slack_webhook'),
                    channel=data.get('slack_channel'),
                    notify_critical=data.get('notify_critical', True),
                    notify_high=data.get('notify_high', True),
                    notify_medium=data.get('notify_medium', False),
                    notify_low=data.get('notify_low', False),
                    notify_scan_failed=data.get('notify_scan_failed', True),
                    notify_daily_summary=data.get('notify_daily_summary', False)
                )
        
        if data.get('teams_webhook'):
            existing_teams = NotificationMapper.get_configuration_by_type_service('chat', 'Teams', group_id)
            
            if existing_teams:
                NotificationMapper.update_configuration(existing_teams.id,
                                                       webhook_url=data.get('teams_webhook'),
                                                       channel=data.get('teams_channel'),
                                                       notify_critical=data.get('notify_critical', True),
                                                       notify_high=data.get('notify_high', True))
                NotificationMapper.create_configuration(
                    name='Teams Notifications',
                    type='chat',
                    service='Teams',
                    group_id=group_id,
                    webhook_url=data.get('teams_webhook'),
                    channel=data.get('teams_channel'),
                    notify_critical=data.get('notify_critical', True),
                    notify_high=data.get('notify_high', True)
                )
        
        if data.get('email_recipients'):
            existing_email = NotificationMapper.get_configuration_by_type_service('email', 'Gmail', group_id)
            
            additional_config = {
                'smtp_server': data.get('email_smtp_server', 'smtp.gmail.com'),
                'smtp_port': int(data.get('email_smtp_port', 587)),
                'username': data.get('email_username', ''),
                'password': data.get('email_password', '')
            }
            
            if existing_email:
                NotificationMapper.update_configuration(existing_email.id,
                                                       channel=data.get('email_recipients'),
                                                       subject_template=data.get('email_subject', '[DockSafe]'),
                                                       notify_critical=data.get('notify_critical', True),
                                                       notify_high=data.get('notify_high', True),
                                                       additional_config=additional_config)
                NotificationMapper.create_configuration(
                    name='Email Notifications',
                    type='email',
                    service='Gmail',
                    group_id=group_id,
                    channel=data.get('email_recipients'),
                    subject_template=data.get('email_subject', '[DockSafe]'),
                    notify_critical=data.get('notify_critical', True),
                    notify_high=data.get('notify_high', True),
                    additional_config=additional_config
                )
    
    @staticmethod
    def test_notifications(group_id, test_type='all'):
        results = {}
        
        if test_type == 'all' or test_type == 'slack':
            from app.notifications.slack_service import create_slack_service
            slack_configs = NotificationMapper.get_configurations_by_group(group_id)
            slack_configs = [c for c in slack_configs if c.type == 'chat' and c.service == 'Slack']
            
            slack_results = []
            for config in slack_configs:
                try:
                    slack_service = create_slack_service(config.webhook_url, config.channel)
                    
                    if slack_service:
                        success = slack_service.send_test_message()
                        slack_results.append({
                            'config_name': config.name,
                            'success': success,
                            'message': 'Test message sent successfully' if success else 'Failed to send test message'
                        })
                    else:
                        slack_results.append({
                            'config_name': config.name,
                            'success': False,
                            'message': 'Invalid webhook URL'
                        })
                except Exception as e:
                    slack_results.append({
                        'config_name': config.name,
                        'success': False,
                        'message': f'Error: {str(e)}'
                    })
            
            results['slack'] = slack_results
        
        if test_type == 'all' or test_type == 'teams':
            teams_configs = NotificationMapper.get_configurations_by_group(group_id)
            teams_configs = [c for c in teams_configs if c.type == 'chat' and c.service == 'Teams']
            
            teams_results = []
            for config in teams_configs:
                teams_results.append({
                    'config_name': config.name,
                    'success': False,
                    'message': 'Teams integration not yet implemented'
                })
            
            results['teams'] = teams_results
        
        if test_type == 'all' or test_type == 'email':
            email_configs = NotificationMapper.get_configurations_by_group(group_id)
            email_configs = [c for c in email_configs if c.type == 'email']
            
            email_results = []
            for config in email_configs:
                email_results.append({
                    'config_name': config.name,
                    'success': False,
                    'message': 'Email integration not yet implemented'
                })
            
            results['email'] = email_results
        
        return results
    @staticmethod
    def get_notification_history(group_id, limit=50):
        return NotificationMapper.get_notification_history(group_id, limit)
