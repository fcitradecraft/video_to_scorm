(async function () {
  scorm.init();
  // Make sure status starts as incomplete if not already set
  const status = scorm.get("cmi.core.lesson_status");
  if (!status || status === "not attempted") scorm.set("cmi.core.lesson_status", "incomplete");

  const form = document.getElementById('qform');
  const submit = document.getElementById('submit');
  const result = document.getElementById('result');
  const qs = await fetch('questions.json').then(r => r.json());

  // Render
  qs.forEach(q => {
    const wrap = document.createElement('section');
    wrap.className = 'item';
    wrap.dataset.qid = q.id;
    wrap.innerHTML = `<h2>${q.stem}</h2>`;
    if (q.type === 'mc') {
      q.choices.forEach((c, idx) => {
        wrap.innerHTML += `<label><input type="radio" name="${q.id}" value="${idx}"> ${c}</label><br>`;
      });
    } else if (q.type === 'rubric') {
      q.criteria.forEach(cr => {
        wrap.innerHTML += `
          <label>${cr.label} (0–${cr.points}): 
            <input type="number" min="0" max="${cr.points}" step="1" name="${q.id}_${cr.id}">
          </label><br>`;
      });
      wrap.innerHTML += `<label>Rationale: <textarea name="${q.id}_text"></textarea></label>`;
    }
    form.appendChild(wrap);
  });

  function recordInteraction(n, q, student, result, weight, latencyMs) {
    scorm.set(`cmi.interactions.${n}.id`, q.id);
    scorm.set(`cmi.interactions.${n}.student_response`, student);
    scorm.set(`cmi.interactions.${n}.result`, result); // correct | wrong | neutral
    scorm.set(`cmi.interactions.${n}.weighting`, weight);
    scorm.set(`cmi.interactions.${n}.latency`, `PT${Math.round(latencyMs/1000)}S`);
  }

  const startTime = Date.now();

  submit.addEventListener('click', () => {
    let score = 0, max = 100, n = 0;

    // Q1 auto-score (50 points)
    const q1 = qs.find(q => q.id === 'q1');
    const chosen = (new FormData(form)).get('q1');
    const correct = (chosen !== null && Number(chosen) === q1.answer);
    score += correct ? 50 : 0;
    recordInteraction(n++, q1, String(chosen), correct ? "correct" : "wrong", 0.5, Date.now()-startTime);

    // Q2 rubric (0–50 points)
    const q2 = qs.find(q => q.id === 'q2');
    const fd = new FormData(form);
    let rubricScore = 0;
    q2.criteria.forEach(cr => rubricScore += Number(fd.get(`${q2.id}_${cr.id}`) || 0));
    if (rubricScore > 50) rubricScore = 50;
    score += rubricScore;

    const rationale = (fd.get(`${q2.id}_text`) || "").toString().slice(0,255);
    recordInteraction(n++, q2, `rubric:${rubricScore}; note:${rationale}`, "neutral", 0.5, Date.now()-startTime);

    // Set SCORM score + status
    scorm.set("cmi.core.score.raw", Math.round(score));
    const passed = score >= 80;
    scorm.set("cmi.core.lesson_status", passed ? "passed" : "failed");
    scorm.commit();

    result.textContent = `Score: ${Math.round(score)} / ${max} — ${passed ? "PASSED" : "FAILED"}`;
    // Finish the attempt (optional: give the learner time to read)
    setTimeout(() => scorm.finish(), 1200);
  });
})();
