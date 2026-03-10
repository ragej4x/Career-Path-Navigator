// Load questions dynamically from the backend
async function loadQuestions() {
  console.log('DEBUG: loadQuestions called');
  try {
    const response = await apiCall('/questions', 'GET');
    console.log('DEBUG: apiCall response:', response);
    if (response.ok && response.data) {
      const questions = response.data;
      console.log('DEBUG: Received questions:', questions);
      renderQuizQuestions(questions);
    } else {
      console.error('Failed to load questions. Response:', response);
    }
  } catch (error) {
    console.error('Error loading questions:', error);
  }
}

function renderQuizQuestions(questions) {
  console.log('DEBUG: renderQuizQuestions called with', questions.length, 'questions');
  const quizContainer = document.getElementById('quizForm');
  console.log('DEBUG: quizForm element:', quizContainer);
  
  if (!quizContainer) {
    console.error('ERROR: Could not find quizForm element');
    return;
  }

  // Clear existing questions
  const existingQuestions = quizContainer.querySelectorAll('[data-question-id]');
  console.log('DEBUG: Clearing', existingQuestions.length, 'existing questions');
  existingQuestions.forEach(q => q.remove());

  // Render questions dynamically
  questions.forEach((q, index) => {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-container';
    questionDiv.setAttribute('data-question-id', q.id);
    
    questionDiv.innerHTML = `
      <div class="question">
        <label>${index + 1}. ${q.question_text}</label>
        <div class="options">
          <label>
            <input type="radio" name="question_${q.id}" value="yes" data-strand="${q.strand}"> Yes
          </label>
          <label>
            <input type="radio" name="question_${q.id}" value="no"> No
          </label>
        </div>
      </div>
    `;
    
    const submitBtn = quizContainer.querySelector('button[type="submit"]');
    quizContainer.insertBefore(questionDiv, submitBtn);
  });
  
  console.log('DEBUG: Questions rendered successfully');
}

// Load questions when the page loads
document.addEventListener('DOMContentLoaded', function() {
  console.log('DEBUG: DOMContentLoaded event fired');
  loadQuestions();
});

if (document.getElementById("quizForm")) {
  document.getElementById("quizForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const submitBtn = this.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Analyzing...';

    // 1. Calculate Scores - Updated for dynamic questions
    let scores = { STEM: 0, HUMSS: 0, ABM: 0, TVL: 0 };
    const answers = document.querySelectorAll("#quizForm input[type=radio]:checked");
    answers.forEach(a => { 
      if (a.value === "yes" && a.dataset.strand) {
        scores[a.dataset.strand]++;
      }
    });

    let highest = Math.max(...Object.values(scores));
    let recommended = Object.keys(scores).filter(s => scores[s] === highest);
    
    // 2. Get AI Tips (Using apiCall)
    let aiTips = '';
    try {
      const tipsRes = await apiCall(`/strand-tips/${recommended[0]}`, 'GET');
      if(tipsRes.ok && tipsRes.data && tipsRes.data.tips) {
        aiTips = tipsRes.data.tips;
      }
    } catch (err) {
      console.error('Error fetching AI tips:', err);
    }
    // 3. Save Result (Using apiCall)
    const resultData = JSON.stringify({
      recommended_strands: recommended,
      scores: scores,
      ai_tips: aiTips,
      timestamp: new Date().toISOString()
    });

    const saveRes = await apiCall('/quiz/save', 'POST', { result_data: resultData });
    
    if (!saveRes.ok) {
      alert('Error saving quiz result: ' + (saveRes.data?.error || 'Unknown error'));
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Get Recommendations';
      return;
    }

    // 4. Display
    const formattedTips = aiTips
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
    
    document.getElementById('results').innerHTML = `
      <h2>Result: ${recommended.join(', ')}</h2>
      <div style="background: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0; line-height: 1.6; color: #555;">
        <h3 style="color: #667eea; margin-top: 0;">🤖 AI Guidance</h3>
        <div>${formattedTips || 'Career guidance is being prepared. Please check your results later.'}</div>
      </div>
      <button class="btn" onclick="location.href='${getStrandUrl(recommended[0])}'">View Courses</button>
    `;
    
    showSection('results');
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Get Recommendations';
  });
}

function getStrandUrl(strand) {
    const map = {
        STEM: 'stem-courses/stem.html',
        HUMSS: 'humss-courses/humss.html',
        ABM: 'abm-courses/abm.html',
        TVL: 'tvl-courses/tvl.html'
    };
    return map[strand] || '#';
}