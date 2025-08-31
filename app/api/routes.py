"""
API routes for DockSafe application
"""

from flask import jsonify
from app.api import bp

@bp.route('/')
def index():
    """API index"""
    return jsonify({
        'name': 'DockSafe API',
        'version': '1.0.0',
        'endpoints': {
            'scanner': '/scanner',
            'reports': '/reports',
            'notifications': '/notifications',
            'dashboard': '/dashboard'
        }
    })
