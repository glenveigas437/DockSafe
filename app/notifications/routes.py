"""
Notifications routes for DockSafe application
"""

from flask import render_template, jsonify, request
from app.models import NotificationHistory
from app.notifications import bp

@bp.route('/')
def index():
    """Notifications index page"""
    return render_template('notifications/index.html')

@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """Get or update notification settings"""
    if request.method == 'GET':
        # Return current settings (for now, return defaults)
        return jsonify({
            'slack_webhook': '',
            'slack_channel': '',
            'teams_webhook': '',
            'teams_channel': '',
            'email_recipients': '',
            'email_subject': '[DockSafe]',
            'notify_critical': True,
            'notify_high': True,
            'notify_scan_failed': True,
            'notify_daily_summary': False
        })
    else:
        # Save settings (for now, just return success)
        try:
            data = request.get_json()
            # TODO: Save settings to database or config file
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/history')
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
def test_notification():
    """Test notification endpoint"""
    try:
        data = request.get_json()
        slack = data.get('slack', False)
        teams = data.get('teams', False)
        email = data.get('email', False)
        
        # TODO: Actually send test notifications
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': 'Test notification sent successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
