// Builds a clickable section list from sections.json and keeps the "current" highlight in sync.
// Usage in video.js:
//   Sidebar.init({ sections, onJump: (t)=>player.currentTime=t });
//   Sidebar.updateByTime(player.currentTime);

window.Sidebar = (function () {
  let sections = [];
  let tocEl = null;

  function build(items) {
    sections = items || [];
    tocEl = document.getElementById('toc');
    if (!tocEl) return;

    tocEl.innerHTML = '';
    sections.forEach((s, i) => {
      const li = document.createElement('li');
      li.innerHTML = `<button type="button" data-i="${i}" data-t="${s.start}">${i + 1}. ${s.title}</button>`;
      tocEl.appendChild(li);
    });
  }

  function on(container, event, sel, handler) {
    container.addEventListener(event, e => {
      const target = e.target.closest(sel);
      if (target && container.contains(target)) handler(e, target);
    });
  }

  function currentIndexByTime(t) {
    for (let i = sections.length - 1; i >= 0; i--) {
      if (t >= sections[i].start) return i;
    }
    return 0;
  }

  function highlight(i) {
    if (!tocEl) return;
    [...tocEl.querySelectorAll('button')].forEach((b, idx) => {
      b.classList.toggle('current', idx === i);
    });
  }

  return {
    init: function ({ sections: secs, onJump }) {
      build(secs);
      if (tocEl) {
        on(tocEl, 'click', 'button', (_e, btn) => {
          const t = parseFloat(btn.dataset.t || '0');
          highlight(parseInt(btn.dataset.i, 10));
          if (typeof onJump === 'function') onJump(t);
        });
      }
    },
    updateByTime: function (t) {
      highlight(currentIndexByTime(t || 0));
    }
  };
})();
