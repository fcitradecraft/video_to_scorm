(async function () {
  // Load sections and wire sidebar
  const sections = await fetch('sections.json').then(r => r.json());
  const player = document.getElementById('player');
  const btnComplete = document.getElementById('btn-complete');

  Sidebar.init({ sections, onJump: t => (player.currentTime = t) });

  // Hook up SCORM
  scorm.init();
  // Restore bookmark + suspend data
  let location = scorm.get("cmi.core.lesson_location");
  let suspend = scorm.get("cmi.suspend_data");
  try { suspend = suspend ? JSON.parse(suspend) : {}; } catch { suspend = {}; }

  if (location) player.currentTime = parseFloat(location);
  Sidebar.updateByTime(player.currentTime || 0);

  // Update bookmark every 5s
  setInterval(() => {
    scorm.set("cmi.core.lesson_location", player.currentTime.toFixed(1));
    const idx = sections.findIndex((s, i) => {
      const next = sections[i + 1];
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
  });

  player.addEventListener('timeupdate', () => {
    Sidebar.updateByTime(player.currentTime);
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
