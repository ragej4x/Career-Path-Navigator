# API Endpoints Reference

## Authentication Routes

### User Registration
```
POST /api/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123"
}

Response: 201
{
  "message": "Registered successfully"
}
```

### User Login
```
POST /api/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123"
}

Response: 200
{
  "message": "Login successful",
  "username": "john_doe"
}
```

### Check User Auth
```
GET /api/check-auth

Response: 200
{
  "authenticated": true,
  "username": "john_doe"
}
```

### User Logout
```
POST /api/logout

Response: 200
{
  "message": "Logged out"
}
```

---

## Quiz Routes

### Get All Questions
```
GET /api/questions

Response: 200
[
  {
    "id": 1,
    "question_text": "Do you enjoy solving math problems?",
    "strand": "STEM",
    "created_at": "2024-03-11T10:30:00"
  },
  {
    "id": 2,
    "question_text": "Are you interested in social sciences?",
    "strand": "HUMSS",
    "created_at": "2024-03-11T10:35:00"
  }
]
```

### Save Quiz Result
```
POST /api/quiz/save
Content-Type: application/json
[Authentication Required]

{
  "result_data": "{\"recommended_strands\":[\"STEM\"],\"scores\":{\"STEM\":15,\"HUMSS\":8,\"ABM\":5,\"TVL\":2},\"ai_tips\":\"...\",\"timestamp\":\"2024-03-11T12:00:00\"}"
}

Response: 201
{
  "message": "Saved"
}
```

### Get Quiz History
```
GET /api/quiz/history
[Authentication Required]

Response: 200
[
  {
    "id": 1,
    "result_data": "{...}",
    "created_at": "2024-03-11T12:00:00"
  }
]
```

### Delete Quiz Result
```
DELETE /api/quiz/delete/<id>
[Authentication Required]

Response: 200
{
  "message": "Deleted"
}
```

---

## Strand & Career Routes

### Get Strand Tips (AI-Powered)
```
GET /api/strand-tips/<strand>

Parameters:
- strand (path): STEM | HUMSS | ABM | TVL

Response: 200
{
  "tips": "Here are the career tips and recommendations for the STEM strand..."
}
```

---

## User Profile Routes

### Get Reflection Notes
```
GET /api/reflection
[Authentication Required]

Response: 200
{
  "reflection_notes": "My career goals are..."
}
```

### Save Reflection Notes
```
POST /api/reflection
Content-Type: application/json
[Authentication Required]

{
  "reflection_notes": "I want to pursue a career in software engineering..."
}

Response: 200
{
  "message": "Saved"
}
```

### Change Password
```
POST /api/change-password
Content-Type: application/json
[Authentication Required]

{
  "current_password": "oldpass123",
  "new_password": "newpass456"
}

Response: 200
{
  "message": "Password changed successfully"
}
```

---

## Admin Routes

### Admin Login
```
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response: 200
{
  "message": "Admin login successful"
}
```

### Check Admin Auth
```
GET /api/admin/check-auth

Response: 200
{
  "authenticated": true,
  "username": "admin"
}
```

### Get All Users
```
GET /api/admin/users
[Admin Authentication Required]

Response: 200
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "N/A"
  },
  {
    "id": 2,
    "username": "jane_smith",
    "email": "jane@example.com",
    "created_at": "N/A"
  }
]
```

### Delete User
```
DELETE /api/admin/delete-user/<user_id>
[Admin Authentication Required]

Response: 200
{
  "message": "User john_doe deleted successfully"
}
```

### Admin Logout
```
POST /api/admin/logout

Response: 200
{
  "message": "Admin logged out"
}
```

---

## Question Management Routes

### Add Question
```
POST /api/admin/questions/add
Content-Type: application/json
[Admin Authentication Required]

{
  "question_text": "Do you enjoy programming?",
  "strand": "STEM"
}

Response: 201
{
  "message": "Question added successfully",
  "id": 10
}
```

### Update Question
```
PUT /api/admin/questions/update/<question_id>
Content-Type: application/json
[Admin Authentication Required]

{
  "question_text": "Updated question text",
  "strand": "HUMSS"
}

Response: 200
{
  "message": "Question updated successfully"
}
```

### Delete Question
```
DELETE /api/admin/questions/delete/<question_id>
[Admin Authentication Required]

Response: 200
{
  "message": "Question deleted successfully"
}
```

---

## System Routes

### Health Check
```
GET /api/health

Response: 200
{
  "status": "healthy",
  "message": "API is running"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required fields: username, email, password"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized"
}
```

### 404 Not Found
```json
{
  "error": "Not found or unauthorized"
}
```

### 409 Conflict
```json
{
  "error": "Username exists"
}
```

### 500 Internal Server Error
```json
{
  "error": "Registration failed: ..."
}
```

---

## Authentication Flow

1. User registers/logs in → Session created
2. Browser stores session cookie automatically
3. Subsequent requests include cookie (credentials: 'include')
4. Server validates session for protected routes
5. Logout clears session

---

## Strand Flag Reference

Each question carries a strand flag indicating which career track it relates to:

| Flag | Full Name | Focus |
|------|-----------|-------|
| STEM | Science, Technology, Engineering, Mathematics | Engineering, IT, Science |
| HUMSS | Humanities and Social Sciences | Arts, Social Studies, Communication |
| ABM | Accountancy, Business, and Management | Accounting, Finance, Business |
| TVL | Technical-Vocational-Livelihood | Trades, Technical Skills |

---

## Base URL

- **Local Development**: `http://localhost:5000/api`
- **Production**: `https://career-path-navigator-ifgu.onrender.com/api`

All requests should include:
```
Content-Type: application/json
ngrok-skip-browser-warning: true
```

Use `credentials: 'include'` in fetch for session cookies.

---

Last Updated: March 2024
