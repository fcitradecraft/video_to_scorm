(function () {
  const player = document.getElementById('player');
  const toc = document.getElementById('toc');
  const completeBtn = document.getElementById('btn-complete');

  function buildToc(sections) {
    sections.forEach(sec => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '#';
      a.textContent = sec.title;
      a.addEventListener('click', e => {
        e.preventDefault();
        player.currentTime = sec.start;
        player.play();
      });
      li.appendChild(a);
      toc.appendChild(li);
    });
  }

  function loadSections() {
    fetch('sections.json')
      .then(res => res.json())
      .then(buildToc)
      .catch(() => {});
  }

  function initScorm() {
    if (!window.scorm) return;
    if (!scorm.init()) return;
    completeBtn.addEventListener('click', () => {
      scorm.set('cmi.core.lesson_status', 'completed');
      scorm.commit();
      alert('Marked complete');
    });
    window.addEventListener('beforeunload', function () {
      scorm.finish();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    loadSections();
    initScorm();
  });
})();
