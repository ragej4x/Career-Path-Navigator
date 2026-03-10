# 🧪 Testing & Verification Guide

## Quick Start Verification

### 1. Backend Verification
Verify the app.py changes are correct:

```bash
cd backend
python -c "import app; print('✓ app.py imports successfully')"
```

### 2. Database Verification
Check that Question model is available:

```bash
python
>>> from app import app, db, Question, User, QuizResult
>>> print('✓ All models imported')
>>> with app.app_context():
...     db.create_all()  # Creates tables if needed
...     print('✓ Database tables created')
>>> exit()
```

### 3. Admin Login Test
```bash
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
✅ Expected: `{"message":"Admin login successful"}`

### 4. Get All Users Test
```bash
curl -X GET http://localhost:5000/api/admin/users
```
✅ Expected: Array of users (or empty array if no users yet)

### 5. Get All Questions Test
```bash
curl -X GET http://localhost:5000/api/questions
```
✅ Expected: Empty array initially `[]` (or populated if questions added)

---

## Manual Testing Workflow

### Step 1: Start the Backend
```bash
cd backend
python app.py
```
You should see:
```
* Running on http://0.0.0.0:5000
* WARNING in app.run(): This is a development server...
```

### Step 2: Open Admin Dashboard
1. Open browser
2. Go to: `http://localhost:5000/admin.html`
3. Login with:
   - Username: `admin`
   - Password: `admin123`

### Step 3: Add Sample Questions
1. Go to "Questions Management" tab
2. Add questions (at least 20):

**STEM Questions (5 examples):**
- "Do you enjoy solving complex mathematical problems?"
- "Are you interested in building software applications?"
- "Do you like conducting scientific experiments?"
- "Would you want a career in computer science?"
- "Do you enjoy working with technology?"

**HUMSS Questions (5 examples):**
- "Do you enjoy studying history and cultures?"
- "Are you passionate about helping people?"
- "Do you like communicating and public speaking?"
- "Would you want to study social sciences?"
- "Do you enjoy creative writing or literature?"

**ABM Questions (5 examples):**
- "Do you have strong mathematical skills?"
- "Are you interested in accounting or finance?"
- "Do you enjoy business management?"
- "Would you like to start your own business?"
- "Do you understand financial concepts?"

**TVL Questions (5 examples):**
- "Do you enjoy hands-on technical work?"
- "Are you skilled with tools and equipment?"
- "Do you prefer learning by doing?"
- "Would you want a technical trade career?"
- "Do you enjoy practical problem-solving?"

### Step 4: View Users
1. Go to "Users Management" tab
2. Should see any registered users
3. Test delete functionality on a test user (optional)

### Step 5: Test Quiz Loading
1. Navigate to the quiz page
2. Questions should load automatically from database
3. Verify strand flags appear: `[STEM]` `[HUMSS]` `[ABM]` `[TVL]`
4. Answer the quiz
5. Submit and verify results
6. Check "My Results" to see saved quiz

---

## API Testing with cURL

### Test Admin Login
```bash
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt

# Response:
# {"message":"Admin login successful"}
```

### Test Add Question
```bash
curl -X POST http://localhost:5000/api/admin/questions/add \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question_text": "Do you enjoy solving math problems?",
    "strand": "STEM"
  }'

# Response:
# {"message":"Question added successfully","id":1}
```

### Test Get Questions
```bash
curl -X GET http://localhost:5000/api/questions

# Response:
# [
#   {
#     "id": 1,
#     "question_text": "Do you enjoy solving math problems?",
#     "strand": "STEM",
#     "created_at": "2024-03-11T12:00:00"
#   }
# ]
```

### Test Get Users (as Admin)
```bash
curl -X GET http://localhost:5000/api/admin/users \
  -b cookies.txt

# Response: Array of users
```

### Test Delete User
```bash
curl -X DELETE http://localhost:5000/api/admin/delete-user/2 \
  -b cookies.txt

# Response:
# {"message":"User <username> deleted successfully"}
```

---

## Automated Test Script

Save as `test_admin.sh`:

```bash
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="http://localhost:5000/api"
COOKIES_FILE="admin_cookies.txt"

echo "🧪 Starting Admin API Tests...\n"

# Test 1: Admin Login
echo "Test 1: Admin Login"
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c $COOKIES_FILE)

if echo $LOGIN_RESPONSE | grep -q "Admin login successful"; then
    echo -e "${GREEN}✓ Admin Login PASSED${NC}\n"
else
    echo -e "${RED}✗ Admin Login FAILED${NC}\n"
    exit 1
fi

# Test 2: Get All Users
echo "Test 2: Get All Users"
USERS_RESPONSE=$(curl -s -X GET $API_URL/admin/users -b $COOKIES_FILE)
if echo $USERS_RESPONSE | grep -q "\["; then
    echo -e "${GREEN}✓ Get Users PASSED${NC}\n"
else
    echo -e "${RED}✗ Get Users FAILED${NC}\n"
fi

# Test 3: Get All Questions
echo "Test 3: Get All Questions"
QUESTIONS_RESPONSE=$(curl -s -X GET $API_URL/questions)
if echo $QUESTIONS_RESPONSE | grep -q "\["; then
    echo -e "${GREEN}✓ Get Questions PASSED${NC}\n"
else
    echo -e "${RED}✗ Get Questions FAILED${NC}\n"
fi

# Test 4: Add Question
echo "Test 4: Add Question"
ADD_RESPONSE=$(curl -s -X POST $API_URL/admin/questions/add \
  -H "Content-Type: application/json" \
  -b $COOKIES_FILE \
  -d '{
    "question_text": "Test question?",
    "strand": "STEM"
  }')

if echo $ADD_RESPONSE | grep -q "Question added"; then
    echo -e "${GREEN}✓ Add Question PASSED${NC}\n"
else
    echo -e "${RED}✗ Add Question FAILED${NC}\n"
fi

# Clean up
rm -f $COOKIES_FILE

echo "🎉 All basic tests completed!"
```

Run it:
```bash
bash test_admin.sh
```

---

## Checklist: Everything Working?

- [ ] Backend app.py runs without errors
- [ ] Database tables created (question, user, quiz_result)
- [ ] Admin login works with credentials
- [ ] Can view users list
- [ ] Can delete users
- [ ] Can add questions via admin dashboard
- [ ] Can view questions list
- [ ] Can delete questions
- [ ] Questions load in quiz form
- [ ] Strand flags display correctly
- [ ] Quiz submission works with dynamic questions
- [ ] Results save to database
- [ ] My Results page shows quiz history

---

## Common Issues & Solutions

### Issue: "Question model not found"
**Solution:** 
```bash
cd backend
python -c "from app import app, db, Question; print('OK')"
# If this fails, restart Flask server
```

### Issue: "Admin login returns 401"
**Solution:**
- Check username is exactly: `admin` (lowercase)
- Check password is exactly: `admin123` (case-sensitive)
- Verify no typos in credentials

### Issue: "No questions loaded in quiz"
**Solution:**
1. Check if questions exist: GET /api/questions
2. Check browser console for errors
3. Verify quizForm has correct ID attribute
4. Check loadQuestions() runs on page load

### Issue: "Questions not rendering with strand flags"
**Solution:**
1. Check each question has `strand` field in response
2. Verify renderQuizQuestions() is creating elements
3. Check CSS isn't hiding the strand flags
4. Inspect page source to see generated HTML

### Issue: "Delete user returns 404"
**Solution:**
- Verify user_id exists in database
- Use GET /api/admin/users to get valid IDs
- Check session is still valid
- Confirm you're logged in as admin

---

## Performance Testing

### Load Testing with 100 Questions
```bash
# Test with large number of questions
for i in {1..100}; do
  curl -s -X POST http://localhost:5000/api/admin/questions/add \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d "{
      \"question_text\": \"Test question $i?\",
      \"strand\": \"$(echo 'STEM HUMSS ABM TVL' | cut -d' ' -f$((i % 4 + 1)))\",
    }" > /dev/null
done

# Then test quiz load time
time curl -s -X GET http://localhost:5000/api/questions > /dev/null
```

Expected: < 100ms for response with 100 questions

---

## Browser DevTools Testing

### Console Tests
```javascript
// Test 1: Check if apiCall function exists
console.log(typeof apiCall);  // Should be 'function'

// Test 2: Check if loadQuestions runs
console.log(document.querySelectorAll('[data-question-id]').length);

// Test 3: Check API response
apiCall('/questions', 'GET').then(res => {
  console.log('Questions:', res.data);
  console.log('Count:', res.data.length);
});

// Test 4: Check for strand flags
console.log(document.querySelectorAll('.strand-flag').length);
```

### Network Tab Testing
1. Open DevTools → Network tab
2. Navigate to admin.html
3. Verify these requests:
   - `admin.html` - 200
   - `/api/admin/check-auth` - 200 or 401 (both OK)
   - `/api/questions` - 200

---

**Last Updated:** March 2024
**Status:** Ready for full implementation testing
