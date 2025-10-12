
from flask import render_template, jsonify, request, session
from app.models import NotificationHistory
from app.notifications import bp
from app.decorators import login_required
from app.services.notification_service import NotificationService

@bp.route('/')
@login_required
def index():
    """Notifications index page"""
    return render_template('notifications/index.html')

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Get or update notification settings"""
    try:
        # Get the selected group ID from session
        group_id = session.get('selected_group_id')
        
        # If no group selected, try to get the user's first group
        if not group_id:
            from app.models import User
            user_id = session.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                if user and user.groups:
                    group_id = user.groups[0].id
                    session['selected_group_id'] = group_id
        
        if not group_id:
            return jsonify({'success': False, 'error': 'No group selected. Please select a group first.'}), 400
        
        if request.method == 'GET':
            # Get current settings from database
            from app.models import NotificationConfiguration
            configs = NotificationConfiguration.query.filter_by(group_id=group_id).all()
            
            # Convert to dict format
            settings = {
                'slack_webhook': '',
                'slack_channel': '',
                'slack_enabled': False,
                'email_recipients': '',
                'email_subject': '[DockSafe]',
                'email_enabled': False,
                'critical_enabled': True,
                'high_enabled': True,
                'failure_enabled': True,
                'new_enabled': False
            }
            
            for config in configs:
                if config.type == 'chat' and config.service == 'Slack':
                    settings['slack_webhook'] = config.webhook_url or ''
                    settings['slack_channel'] = config.channel or ''
                    settings['slack_enabled'] = config.is_active
                elif config.type == 'email':
                    settings['email_recipients'] = config.email_recipients or ''
                    settings['email_enabled'] = config.is_active
            
            return jsonify(settings)
        else:
            # Save settings to database
            data = request.get_json()
            
            from app.models import NotificationConfiguration, db
            
            # Delete existing configurations for this group
            NotificationConfiguration.query.filter_by(group_id=group_id).delete()
            
            # Create Slack configuration if enabled
            if data.get('slack_enabled') and data.get('slack_webhook'):
                slack_config = NotificationConfiguration(
                    name='Slack Notifications',
                    type='chat',
                    service='Slack',
                    group_id=group_id,
                    webhook_url=data.get('slack_webhook'),
                    channel=data.get('slack_channel', '#general'),
                    is_active=True
                )
                db.session.add(slack_config)
            
            # Create Email configuration if enabled
            if data.get('email_enabled') and data.get('email_recipients'):
                email_config = NotificationConfiguration(
                    name='Email Notifications',
                    type='email',
                    service='Gmail',
                    group_id=group_id,
                    email_recipients=data.get('email_recipients'),
                    is_active=True
                )
                db.session.add(email_config)
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/history')
@login_required
def history():
    """Get notification history"""
    try:
        # Get recent notifications (for now, return empty list)
        # TODO: Query actual notification history from database
        notifications = []
        
        return jsonify({'notifications': notifications})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Test notification endpoint"""
    try:
        # Get the selected group ID from session
        group_id = session.get('selected_group_id')
        
        # If no group selected, try to get the user's first group
        if not group_id:
            from app.models import User
            user_id = session.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                if user and user.groups:
                    group_id = user.groups[0].id
                    session['selected_group_id'] = group_id
        
        if not group_id:
            return jsonify({'success': False, 'error': 'No group selected. Please select a group first.'}), 400
        
        data = request.get_json()
        slack = data.get('slack', False)
        teams = data.get('teams', False)
        email = data.get('email', False)
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Test notifications based on what was requested
        test_type = 'all'
        if slack and not teams and not email:
            test_type = 'slack'
        elif teams and not slack and not email:
            test_type = 'teams'
        elif email and not slack and not teams:
            test_type = 'email'
        
        results = notification_service.test_notifications(group_id, test_type=test_type)
        
        return jsonify({
            'success': True,
            'message': 'Test notifications sent successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/test/slack', methods=['POST'])
@login_required
def test_slack_notification():
    """Test Slack notification specifically"""
    try:
        # Get the selected group ID from session
        group_id = session.get('selected_group_id')
        
        # If no group selected, try to get the user's first group
        if not group_id:
            from app.models import User
            user_id = session.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                if user and user.groups:
                    group_id = user.groups[0].id
                    session['selected_group_id'] = group_id
        
        if not group_id:
            return jsonify({'success': False, 'error': 'No group selected. Please select a group first.'}), 400
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Test Slack notification
        results = notification_service.test_notifications(group_id, test_type='slack')
        
        if results.get('slack'):
            slack_results = results['slack']
            if slack_results and any(result.get('success', False) for result in slack_results):
                return jsonify({
                    'success': True,
                    'message': 'Slack test notification sent successfully',
                    'results': slack_results
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to send Slack notification',
                    'results': slack_results
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'No Slack configuration found. Please configure Slack webhook first.'
            }), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
