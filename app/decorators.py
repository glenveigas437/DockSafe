from functools import wraps
from flask import redirect, url_for, session, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Invalid session'}), 401
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def jwt_required_optional(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return jwt_required()(f)(*args, **kwargs)
        except:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
    return decorated_function
