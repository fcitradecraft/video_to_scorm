(async function () {
  // Load sections for sidebar
  const sections = await fetch('sections.json').then(r => r.json());
  const toc = document.getElementById('toc');
  const player = document.getElementById('player');
  const btnComplete = document.getElementById('btn-complete');

  // Build sidebar
  sections.forEach((s, i) => {
    const li = document.createElement('li');
    li.innerHTML = `<button data-t="${s.start}">${i+1}. ${s.title}</button>`;
    toc.appendChild(li);
  });

  // Hook up SCORM
  scorm.init();
  // Restore bookmark + suspend data
  let location = scorm.get("cmi.core.lesson_location"); // seconds
  let suspend = scorm.get("cmi.suspend_data");          // JSON string
  try { suspend = suspend ? JSON.parse(suspend) : {}; } catch { suspend = {}; }

  if (location) player.currentTime = parseFloat(location);
  // optional: highlight last section
  if (suspend.currentSection !== undefined) {
    [...toc.querySelectorAll('button')].forEach((b, i) => {
      if (i === suspend.currentSection) b.classList.add('current');
    });
  }

  // Sidebar click → seek
  toc.addEventListener('click', e => {
    if (e.target.tagName === 'BUTTON') {
      const t = parseFloat(e.target.dataset.t || "0");
      player.currentTime = t;
    }
  });

  // Update bookmark every 5s
  setInterval(() => {
    scorm.set("cmi.core.lesson_location", player.currentTime.toFixed(1));
    // figure out current section by time
    const idx = sections.findIndex((s, i) => {
      const next = sections[i+1]; 
      return player.currentTime >= s.start && (!next || player.currentTime < next.start);
    });
    const pct = (player.currentTime / (player.duration || 1)) * 100;
    const data = { currentSection: idx < 0 ? 0 : idx, percentWatched: Math.min(100, Math.round(pct)) };
    scorm.set("cmi.suspend_data", JSON.stringify(data).slice(0, 4000));
    scorm.commit();
  }, 5000);

  // Mark complete button (or auto-complete at 90% watched)
  btnComplete.addEventListener('click', () => {
    scorm.set("cmi.core.lesson_status", "completed");
    scorm.commit();
    scorm.finish();
    // Optionally navigate the LMS back
  });

  player.addEventListener('timeupdate', () => {
    if (player.duration && player.currentTime / player.duration >= 0.9) {
      scorm.set("cmi.core.lesson_status", "completed");
    }
  });

  // On unload, save & close
  window.addEventListener('beforeunload', () => {
    scorm.set("cmi.core.lesson_location", player.currentTime.toFixed(1));
    scorm.commit();
    scorm.finish();
  });
})();
