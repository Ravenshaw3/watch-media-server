"""
Authentication API Routes
Handles user registration, login, logout, and authentication
"""

from flask import Blueprint, request, jsonify
from src.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def init_auth_routes(app, auth_service):
    """Initialize authentication routes"""
    
    @auth_bp.route('/login', methods=['POST'])
    def api_login():
        """User login endpoint"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = auth_service.authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = auth_service.generate_token(user['id'], user['username'], user['role'])
        
        response = jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'preferences': user['preferences']
            }
        })
        
        # Set secure cookie
        response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Strict')
        
        return response

    @auth_bp.route('/register', methods=['POST'])
    def api_register():
        """User registration endpoint"""
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        try:
            user = auth_service.create_user(username, email, password)
            token = auth_service.generate_token(user['id'], user['username'], user['role'])
            
            response = jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'preferences': user['preferences']
                }
            })
            
            response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Strict')
            return response
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Registration failed'}), 500

    @auth_bp.route('/logout', methods=['POST'])
    def api_logout():
        """User logout endpoint"""
        response = jsonify({'message': 'Logged out successfully'})
        response.set_cookie('access_token', '', expires=0)
        return response

    @auth_bp.route('/me')
    def api_get_current_user():
        """Get current user info"""
        # For now, return a simple response
        # In a full implementation, this would validate JWT tokens
        return jsonify({'error': 'Authentication not fully implemented'}), 401

    @auth_bp.route('/preferences', methods=['PUT'])
    def api_update_preferences():
        """Update user preferences"""
        # This would need to be implemented with proper JWT token validation
        # For now, returning a placeholder
        return jsonify({'error': 'Not implemented'}), 501

    # Register the blueprint
    app.register_blueprint(auth_bp)
