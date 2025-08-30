(async function () {
  const form = document.getElementById('qform');
  const btn = document.getElementById('submit');
  const result = document.getElementById('result');

  // Load questions
  const questions = await fetch('questions.json').then(r => r.json());

  // Build form
  questions.forEach((q, i) => {
    const fs = document.createElement('fieldset');
    const legend = document.createElement('legend');
    legend.textContent = `${i + 1}. ${q.question}`;
    fs.appendChild(legend);
    q.options.forEach((opt, j) => {
      const label = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = `q${i}`;
      input.value = j;
      label.appendChild(input);
      label.appendChild(document.createTextNode(opt));
      fs.appendChild(label);
    });
    form.appendChild(fs);
  });

  // Init SCORM
  scorm.init();

  btn.addEventListener('click', e => {
    e.preventDefault();
    let correct = 0;
    questions.forEach((q, i) => {
      const ans = form.querySelector(`input[name=q${i}]:checked`);
      if (ans && parseInt(ans.value, 10) === q.answer) correct++;
    });
    const score = Math.round((correct / questions.length) * 100);
    result.textContent = `Score: ${score}%`;
    scorm.set('cmi.core.score.raw', score);
    const status = score >= 80 ? 'passed' : 'failed';
    scorm.set('cmi.core.lesson_status', status);
    scorm.commit();
    if (status === 'passed') scorm.finish();
  });
})();
