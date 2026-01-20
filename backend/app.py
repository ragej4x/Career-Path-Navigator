from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///career_sydstem.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CRITICAL COOKIE SETTINGS ---
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 
app.config['SESSION_COOKIE_SECURE'] = False  # False is required for HTTP (not HTTPS)
app.config['SESSION_COOKIE_HTTPONLY'] = True 
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# --- Gemini AI Setup ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    GEMINI_API_KEY = 'AIzaSyB03C_gu7H9Lt7AY4Cr6_Qm3vvazQk4x18'
    genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini AI library not found.")

db = SQLAlchemy(app)

# --- CORS: Allow Frontend to talk to Backend ---
# This allows cookies (credentials) to pass between localhost:5500 and localhost:5000
CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": [
            "http://127.0.0.1:5500",  # VS Code Live Server (IP)
            "http://localhost:5500",  # VS Code Live Server (Name)
            "http://127.0.0.1:8000",  # Python Simple Server
            "http://localhost:8000"
            "https://perpetuable-mable-slumberously.ngrok-free.dev"
        ],
        "methods": ["GET", "POST", "OPTIONS", "DELETE", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

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

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'error': 'Username exists'}), 409
    
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    # Auto-login after register
    session.permanent = True
    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'message': 'Login successful', 'username': user.username}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session['username']}), 200
    return jsonify({'authenticated': False}), 401

@app.route('/api/quiz/save', methods=['POST'])
def save_quiz():
    data = request.get_json()
    user_id = session.get('user_id') # Will be None if not logged in
    
    new_result = QuizResult(user_id=user_id, result_data=data['result_data'])
    db.session.add(new_result)
    db.session.commit()
    return jsonify({'message': 'Saved'}), 201

@app.route('/api/quiz/history', methods=['GET'])
def get_history():
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

@app.route('/api/quiz/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_quiz(id):
    result = QuizResult.query.get(id)
    if result and result.user_id == session['user_id']:
        db.session.delete(result)
        db.session.commit()
        return jsonify({'message': 'Deleted'}), 200
    return jsonify({'error': 'Not found or unauthorized'}), 404

@app.route('/api/reflection', methods=['GET', 'POST'])
@login_required
def handle_reflection():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.reflection_notes = request.json.get('reflection_notes', '')
        db.session.commit()
        return jsonify({'message': 'Saved'}), 200
        
    return jsonify({'reflection_notes': user.reflection_notes}), 200

# --- NEW: Add change-password endpoint ---
@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    if not user.check_password(data.get('current_password')):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    if len(data.get('new_password', '')) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    
    user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200

# --- Simple AI Proxy ---
@app.route('/api/strand-tips/<strand>', methods=['GET'])
def get_tips(strand):
    # If Gemini is available, use it
    if GEMINI_AVAILABLE and 'genai' in globals():
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""You are a helpful career guidance counselor. A student has been recommended for the {strand} strand based on their career aptitude quiz.

Please provide:
1. A brief explanation of why this strand suits them (2-3 sentences)
2. Top 3 key skills they should develop
3. Top 5 potential career paths in this field
4. Tips for excelling in this strand
5. Opportunity and benefits
Format your response as clear and short, concise bullet points. Be encouraging and motivational."""
            response = model.generate_content(prompt)
            return jsonify({'tips': response.text})
        except Exception as e:
            print(f"AI Error: {e}")
            
    # Fallback if AI fails or not installed
    return jsonify({'tips': f"Explore careers in {strand}. It offers great opportunities!"})

# --- Health check endpoint ---
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)