"""
Dashboard routes for DockSafe application
"""

from flask import render_template, jsonify
from app.scanner.service import ScannerService

from app.dashboard import bp

@bp.route('/')
def index():
    """Dashboard index page"""
    return render_template('dashboard/index.html')

@bp.route('/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        scanner_service = ScannerService()
        stats = scanner_service.get_scan_statistics(days=30)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
