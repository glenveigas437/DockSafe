"""
Main routes for DockSafe application
"""

from flask import render_template, current_app, jsonify
from app.main import bp
from app.scanner.service import ScannerService

@bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@bp.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check scanner availability
        scanner_service = ScannerService()
        scanner_available = scanner_service.is_scanner_available()
        
        return jsonify({
            'status': 'healthy',
            'scanner_available': scanner_available,
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/dashboard')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')
