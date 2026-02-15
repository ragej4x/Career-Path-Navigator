from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

import os

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///career_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------------------------------------
# SESSION / COOKIE CONFIG
# -------------------------------------------------
app.config['SESSION_COOKIE_SECURE'] = False     # False for local HTTP, True for HTTPS/Ngrok
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # Lax for local testing, None for Ngrok
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_NAME'] = 'career_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    GEMINI_API_KEY = 'AIzaSyC-GZnRcG95eG0p4tnN_7U25hyxbIY8Idg'
    genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini AI library not found.")

db = SQLAlchemy(app)

# --- CORS Configuration ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "https://ragej4x.github.io",
    "https://perpetuable-mable-slumberously.ngrok-free.dev"
]

CORS(
    app,
    supports_credentials=True,
    origins=origins,
    allow_headers=["Content-Type", "Authorization", "ngrok-skip-browser-warning"],
    methods=["GET", "POST", "OPTIONS", "DELETE", "PUT", "PATCH"]
)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    reflection_notes = db.Column(db.Text, default='')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    result_data = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helper function for authentication ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Handle all exceptions and return proper CORS headers"""
    print(f"Error: {error}")
    return jsonify({'error': str(error)}), 500

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields: username, email, password'}), 400
        
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'error': 'Username exists'}), 409
        
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        # Auto-login after register
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'message': 'Registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data.get('username')).first()
        
        if user and user.check_password(data.get('password')):
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'message': 'Login successful', 'username': user.username}), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 204
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@app.route('/api/check-auth', methods=['GET', 'OPTIONS'])
def check_auth():
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session['username']}), 200
    return jsonify({'authenticated': False}), 401

@app.route('/api/quiz/save', methods=['POST', 'OPTIONS'])
def save_quiz():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        new_result = QuizResult(user_id=user_id, result_data=data['result_data'])
        db.session.add(new_result)
        db.session.commit()
        return jsonify({'message': 'Saved'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/history', methods=['GET', 'OPTIONS'])
def get_history():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user_id = session.get('user_id')
        if user_id:
            results = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.created_at.desc()).all()
        else:
            results = QuizResult.query.filter_by(user_id=None).order_by(QuizResult.created_at.desc()).limit(5).all()
            
        return jsonify([{
            'id': r.id,
            'result_data': r.result_data,
            'created_at': r.created_at.isoformat()
        } for r in results]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/delete/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_quiz(id):
    if request.method == 'OPTIONS':
        return '', 204
    
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        result = QuizResult.query.get(id)
        if result and result.user_id == session['user_id']:
            db.session.delete(result)
            db.session.commit()
            return jsonify({'message': 'Deleted'}), 200
        return jsonify({'error': 'Not found or unauthorized'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reflection', methods=['GET', 'POST', 'OPTIONS'])
def handle_reflection():
    if request.method == 'OPTIONS':
        return '', 204
    
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        if request.method == 'POST':
            user.reflection_notes = request.json.get('reflection_notes', '')
            db.session.commit()
            return jsonify({'message': 'Saved'}), 200
            
        return jsonify({'reflection_notes': user.reflection_notes}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/change-password', methods=['POST', 'OPTIONS'])
def change_password():
    if request.method == 'OPTIONS':
        return '', 204
    
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user = User.query.get(session['user_id'])
        
        if not user.check_password(data.get('current_password')):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        if len(data.get('new_password', '')) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/strand-tips/<strand>', methods=['GET', 'OPTIONS'])
def get_tips(strand):
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if GEMINI_AVAILABLE and 'genai' in globals():
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""You are a helpful career guidance counselor. A student has been recommended for the {strand} strand based on their career aptitude quiz.

Please provide:
1. A brief explanation of why this strand suits them (2-3 sentences)
2. Top 3 key skills they should develop
3. Top 5 potential career paths in this field
4. Tips for excelling in this strand
5. Opportunity and benefits
Use bullet points where appropriate, Be encouraging, clear and student-friendly, DO NOT GIVE a one-sentence or overly short answer."""
            response = model.generate_content(prompt)
            return jsonify({'tips': response.text})
    except Exception as e:
        print(f"AI Error: {e}")
    
    # Fallback if AI fails or not installed
    return jsonify({'tips': f"Explore careers in {strand}. It offers great opportunities!"}), 200

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9000)
