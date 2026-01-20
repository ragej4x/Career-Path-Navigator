document.getElementById("quizForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  const submitBtn = this.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.innerHTML = 'Analyzing...';

  // 1. Calculate Scores
  let scores = { STEM: 0, HUMSS: 0, ABM: 0, TVL: 0 };
  const answers = document.querySelectorAll("#quizForm input[type=radio]:checked");
  answers.forEach(a => { if(a.value === "yes" && a.dataset.strand) scores[a.dataset.strand]++; });

  let highest = Math.max(...Object.values(scores));
  let recommended = Object.keys(scores).filter(s => scores[s] === highest);
  
  // 2. Get AI Tips (Using apiCall)
  let aiTips = '';
  const tipsRes = await apiCall(`/strand-tips/${recommended[0]}`, 'GET');
  if(tipsRes.ok) aiTips = tipsRes.data.tips;

  // 3. Save Result (Using apiCall)
  const resultData = JSON.stringify({
    recommended_strands: recommended,
    scores: scores,
    ai_tips: aiTips,
    timestamp: new Date().toISOString()
  });

  await apiCall('/quiz/save', 'POST', { result_data: resultData });

  // 4. Display
  document.getElementById('results').innerHTML = `
    <h2>Result: ${recommended.join(', ')}</h2>
    <p>${aiTips}</p>
    <button class="btn" onclick="location.href='${getStrandUrl(recommended[0])}'">View Courses</button>
  `;
  
  showSection('results');
  submitBtn.disabled = false;
  submitBtn.innerHTML = 'Get Recommendations';
});

function getStrandUrl(strand) {
    const map = {
        STEM: 'stem-courses/stem.html',
        HUMSS: 'humss-courses/humss.html',
        ABM: 'abm-courses/abm.html',
        TVL: 'tvl-courses/tvl.html'
    };
    return map[strand] || '#';
}