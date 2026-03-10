
from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

import os

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'M4QGSqZebCuBjpFIBCMGjTGzcODl5vG6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rpn:IypUU9J2WgdcTXSnGhrL3jHiilSwQzAs@dpg-d6o4h5jh46gs73a6jul0-a.singapore-postgres.render.com/rpn'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------------------------------------
# SESSION / COOKIE CONFIG
# -------------------------------------------------
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
  # Lax for local testing, None for Ngrok
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_NAME'] = 'career_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    GEMINI_API_KEY = 'AIzaSyBx92uzp6kRo1bWEhU__UdHQWwHw4HgDuw'
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
    "https://career-path-navigator-ifgu.onrender.com",
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
    result_data = db.Column(db.Text, nullable=False)  # Changed from String(1000) to Text to store full AI responses
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    strand = db.Column(db.String(50), nullable=False)  # STEM, HUMSS, ABM, TVL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Helper function for authentication ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow OPTIONS requests (CORS preflight) without authentication
        if request.method == 'OPTIONS':
            return '', 204
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Admin authentication ---
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow OPTIONS requests (CORS preflight) without authentication
        if request.method == 'OPTIONS':
            return '', 204
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Admin access required'}), 401
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

# --- STATIC FILES ROUTES (HTML/CSS/JS) ---
@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')

@app.route('/<path:filepath>')
def serve_static(filepath):
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(parent_dir, filepath)
    
    # Security check: ensure the requested file is within the allowed directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(parent_dir)):
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if file exists
    if os.path.isfile(full_path):
        return send_from_directory(parent_dir, filepath)
    
    # If not found, return 404
    return jsonify({'error': 'File not found'}), 404

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
        
        # DEBUG logging
        print(f"DEBUG save_quiz user_id={user_id} data={data}")
        new_result = QuizResult(user_id=user_id, result_data=data['result_data'])
        db.session.add(new_result)
        db.session.commit()
        return jsonify({'message': 'Saved'}), 201
    except Exception as e:
        db.session.rollback()
        print(f"ERROR save_quiz: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/history', methods=['GET', 'OPTIONS'])
def get_history():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user_id = session.get('user_id')
        print(f"DEBUG get_history user_id={user_id}")
        if user_id:
            results = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.created_at.desc()).all()
        else:
            results = QuizResult.query.filter_by(user_id=None).order_by(QuizResult.created_at.desc()).limit(5).all()
            
        print(f"DEBUG get_history returning {len(results)} records")
        for r in results:
            print(f"  record {r.id}: {r.result_data[:100]}...")
        return jsonify([{
            'id': r.id,
            'result_data': r.result_data,
            'created_at': r.created_at.isoformat()
        } for r in results]), 200
    except Exception as e:
        print(f"ERROR get_history: {str(e)}")
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
        if not GEMINI_AVAILABLE:
            print("Gemini not available")
            return jsonify({'tips': f"Career guidance for {strand} strand: Explore the many opportunities available in this field. Consider visiting career counselors for personalized guidance."}), 200
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""You are a career guidance counselor. A student is suited for the {strand} strand.

Provide ONLY the following - be BRIEF and CONCISE:

**Why This Strand Suits You** (2-3 sentences max)

**Top 3 Key Skills to Develop**
- Skill 1
- Skill 2
- Skill 3

**Top 5 Career Paths**
- Career 1
- Career 2
- Career 3
- Career 4
- Career 5

**Tips for Excelling** (2-3 bullet points)
- Tip 1
- Tip 2
- Tip 3

**Opportunities & Benefits** (2-3 bullet points)
- Benefit 1
- Benefit 2
- Benefit 3

Keep it encouraging and student-friendly. NO extra text or explanations."""
        
        response = model.generate_content(prompt)
        tips_text = response.text if hasattr(response, 'text') else str(response)
        
        if not tips_text:
            print("Empty response from Gemini")
            return jsonify({'tips': f"Career guidance for {strand} strand: Explore the many opportunities available in this field."}), 200
            
        return jsonify({'tips': tips_text}), 200
        
    except Exception as e:
        print(f"AI Error for strand {strand}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'tips': f"Career guidance for {strand} strand: Explore the many opportunities available in this field. Consider visiting career counselors for personalized guidance."}), 200

# --- ADMIN ROUTES ---
@app.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({'message': 'Admin login successful'}), 200
        
        return jsonify({'error': 'Invalid admin credentials'}), 401
    except Exception as e:
        return jsonify({'error': f'Admin login failed: {str(e)}'}), 500

@app.route('/api/admin/check-auth', methods=['GET', 'OPTIONS'])
def admin_check_auth():
    if request.method == 'OPTIONS':
        return '', 204
    if 'admin_logged_in' in session:
        return jsonify({'authenticated': True, 'username': session['admin_username']}), 200
    return jsonify({'authenticated': False}), 401

@app.route('/api/admin/users', methods=['GET', 'OPTIONS'])
@admin_required
def get_all_users():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'created_at': 'N/A'  # Add created_at to User model if needed
        } for u in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/delete-user/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@admin_required
def delete_user(user_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete associated quiz results
        QuizResult.query.filter_by(user_id=user_id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'User {user.username} deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logout', methods=['POST', 'OPTIONS'])
def admin_logout():
    if request.method == 'OPTIONS':
        return '', 204
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'message': 'Admin logged out'}), 200

# --- QUESTION MANAGEMENT ROUTES ---
@app.route('/api/questions', methods=['GET', 'OPTIONS'])
def get_questions():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        questions = Question.query.all()
        print(f"DEBUG: Found {len(questions)} questions in database")
        for q in questions:
            print(f"DEBUG: Question {q.id}: {q.question_text[:50]}... (strand: {q.strand})")
        return jsonify([{
            'id': q.id,
            'question_text': q.question_text,
            'strand': q.strand,
            'created_at': q.created_at.isoformat()
        } for q in questions]), 200
    except Exception as e:
        print(f"ERROR in get_questions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/questions/add', methods=['POST', 'OPTIONS'])
@admin_required
def add_question():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data.get('question_text') or not data.get('strand'):
            return jsonify({'error': 'Missing question_text or strand'}), 400
        
        question = Question(
            question_text=data['question_text'],
            strand=data['strand']
        )
        db.session.add(question)
        db.session.commit()
        
        return jsonify({
            'message': 'Question added successfully',
            'id': question.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/questions/update/<int:question_id>', methods=['PUT', 'OPTIONS'])
@admin_required
def update_question(question_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        question = Question.query.get(question_id)
        
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'strand' in data:
            question.strand = data['strand']
        
        db.session.commit()
        return jsonify({'message': 'Question updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/questions/delete/<int:question_id>', methods=['DELETE', 'OPTIONS'])
@admin_required
def delete_question(question_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        db.session.delete(question)
        db.session.commit()
        return jsonify({'message': 'Question deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        #db.drop_all() 
        db.create_all()
        
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))






