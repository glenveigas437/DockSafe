"""
Notifications routes for DockSafe application
"""

from flask import render_template, jsonify

from app.notifications import bp

@bp.route('/')
def index():
    """Notifications index page"""
    return render_template('notifications/index.html')

@bp.route('/test', methods=['POST'])
def test_notification():
    """Test notification endpoint"""
    # TODO: Implement notification testing
    return jsonify({'message': 'Notification testing not yet implemented'}), 501
