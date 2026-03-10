# 🔐 Admin Dashboard & Dynamic Questions Guide

## Overview
Added admin functionality with user management and dynamic quiz questions for Career Path Navigator.

---

## Admin Access

### Login Credentials
```
Username: admin
Password: admin123
```

### Access URL
```
http://localhost:5000/admin.html
or
https://career-path-navigator-ifgu.onrender.com/admin.html
```

---

## Features

### 1. **User Management**
- **View All Users**: See complete list of registered users with their details
- **Delete Users**: Remove users from the system (cascade deletes their quiz results)

#### API Endpoints
```
GET    /api/admin/users
DELETE /api/admin/delete-user/<user_id>
```

**Example: Delete User**
```bash
curl -X DELETE https://yourapi.com/api/admin/delete-user/5 \
  -H "Content-Type: application/json" \
  -c cookies.txt -b cookies.txt
```

---

### 2. **Dynamic Quiz Questions**
Questions are now stored in the database and can be managed without hardcoding.

#### Question Structure
```Python
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    strand = db.Column(db.String(50), nullable=False)  # STEM, HUMSS, ABM, TVL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Strand Flags
Each question is tagged with its strand:
- `STEM` - Science, Technology, Engineering, Mathematics
- `HUMSS` - Humanities and Social Sciences
- `ABM` - Accountancy, Business, and Management
- `TVL` - Technical-Vocational-Livelihood

#### API Endpoints
```
GET    /api/questions                              # Get all questions
POST   /api/admin/questions/add                    # Add new question (Admin)
PUT    /api/admin/questions/update/<question_id>  # Update question (Admin)
DELETE /api/admin/questions/delete/<question_id>  # Delete question (Admin)
```

---

## Admin Dashboard Features

### 📊 User Management Tab
1. **View All Users**
   - ID, Username, Email displayed in table
   - Real-time updates

2. **Delete Users**
   - Confirmation dialog before deletion
   - Automatic cascade deletion of user's quiz results

### ❓ Questions Management Tab
1. **Add Questions**
   - Input: Question text (up to 500 characters)
   - Select strand: STEM, HUMSS, ABM, or TVL
   - One-click addition

2. **View All Questions**
   - Question ID, text, and strand flag
   - Color-coded strand badges

3. **Delete Questions**
   - Confirmation dialog
   - Immediate removal from database

---

## How Quiz Questions Work Now

### Frontend (quiz.js)
```javascript
// 1. Load questions dynamically on page load
async function loadQuestions() {
  const response = await apiCall('/questions', 'GET');
  if (response.ok) {
    renderQuizQuestions(response.data);
  }
}

// 2. Render questions with strand flags
function renderQuizQuestions(questions) {
  // Creates dynamic form with:
  // - Question text
  // - Strand flag [STEM] [HUMSS] [ABM] [TVL]
  // - Yes/No radio buttons
}

// 3. Scoring still tracks strand responses
let scores = { STEM: 0, HUMSS: 0, ABM: 0, TVL: 0 };
answers.forEach(a => { 
  if (a.value === "yes" && a.dataset.strand) {
    scores[a.dataset.strand]++;  // Increment strand score
  }
});
```

---

## API Authentication

### Admin Routes
All admin routes require session authentication:
```bash
# 1. Login as admin
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt  # Save cookies

# 2. Use cookies for subsequent requests
curl -X GET http://localhost:5000/api/admin/users \
  -b cookies.txt  # Include cookies
```

### Admin Login Endpoint
```
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response (200):
{
  "message": "Admin login successful"
}
```

### Check Admin Auth
```
GET /api/admin/check-auth

Response (200):
{
  "authenticated": true,
  "username": "admin"
}

Response (401):
{
  "authenticated": false
}
```

---

## Database Changes

### New Table: Question
```sql
CREATE TABLE question (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  question_text VARCHAR(500) NOT NULL,
  strand VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_strand ON question(strand);
```

---

## Example Usage

### Adding Questions via API
```bash
curl -X POST http://localhost:5000/api/admin/questions/add \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question_text": "Do you enjoy solving complex mathematical problems?",
    "strand": "STEM"
  }'
```

### Updating a Question
```bash
curl -X PUT http://localhost:5000/api/admin/questions/update/1 \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question_text": "Updated question text",
    "strand": "HUMSS"
  }'
```

### Fetching Questions for Quiz
```bash
curl -X GET http://localhost:5000/api/questions
```

Response:
```json
[
  {
    "id": 1,
    "question_text": "Do you enjoy working with numbers?",
    "strand": "ABM",
    "created_at": "2024-03-11T10:30:00"
  },
  {
    "id": 2,
    "question_text": "Are you interested in building software?",
    "strand": "STEM",
    "created_at": "2024-03-11T10:35:00"
  }
]
```

---

## Security Notes

⚠️ **Important:**
1. **Hardcoded Admin Credentials**: Currently using hardcoded `admin` / `admin123`
   - Consider changing these in `app.py` if deploying
   - Better: Use environment variables
   
2. **Session Security**: Admin sessions use Flask sessions with:
   - HTTP-only cookies
   - Secure flag (HTTPS only in production)
   - 7-day expiration

3. **CORS Enabled**: Admin endpoints accessible from configured origins

---

## Upcoming Enhancements

- [ ] Change admin password
- [ ] Multiple admin accounts with roles
- [ ] Question categories/topics
- [ ] Quiz performance analytics
- [ ] Export user data
- [ ] Question bulk import/export

---

## Troubleshooting

### Admin login not working
- Verify username is `admin` (case-sensitive)
- Verify password is `admin123` (case-sensitive)
- Check browser cookies are enabled
- Ensure API base URL is correct in auth.js

### Questions not loading in quiz
- Check `/api/questions` endpoint returns data
- Verify quiz form has `id="quizForm"`
- Check browser console for errors
- Ensure loadQuestions() is called on page load

### Can't delete users
- Ensure you're logged in as admin
- Check session cookie is valid
- Verify user_id is numeric and exists
- Check network tab for 401 responses

---

## File Structure

```
Career-Path-Navigator/
├── admin.html (NEW)
├── quiz.js (UPDATED)
├── auth.js (unchanged)
├── backend/
│   ├── app.py (UPDATED)
│   └── requirements.txt (unchanged)
```

---

For more information, see:
- [Backend Documentation](BACKEND_SETUP.md)
- [Architecture](ARCHITECTURE.md)
