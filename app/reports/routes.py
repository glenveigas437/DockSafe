"""
Reports routes for DockSafe application
"""

from flask import render_template, jsonify

from app.reports import bp

@bp.route('/')
def index():
    """Reports index page"""
    return render_template('reports/index.html')

@bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a new report"""
    # TODO: Implement report generation
    return jsonify({'message': 'Report generation not yet implemented'}), 501
