// Tries to load a PDF fallback if it exists; otherwise shows guidance.
// Optionally records a simple "reviewed" status to SCORM if available.

(function () {
  const pdfPath = "../assets/FCX4_Advanced_Formulas.pdf";
  const frame = document.getElementById('frame');
  const fallback = document.getElementById('fallback');
  const openPdf = document.getElementById('openPdf');
  const btnReviewed = document.getElementById('btn-reviewed');

  // Try to detect a PDF file packaged with the course
  fetch(pdfPath, { method: 'HEAD' })
    .then(r => {
      if (r.ok) {
        frame.src = pdfPath; // most browsers render inline
        openPdf.hidden = false;
        openPdf.href = pdfPath;
      } else {
        frame.src = "about:blank";
        fallback.hidden = false;
      }
    })
    .catch(() => {
      frame.src = "about:blank";
      fallback.hidden = false;
    });

  // Optional SCORM touchpoints (works if page is inside a SCO; otherwise harmless)
  try { window.scorm && window.scorm.init(); } catch {}

  btnReviewed.addEventListener('click', () => {
    if (window.scorm) {
      // Soft-completion marker for slides asset
      const prior = window.scorm.get("cmi.suspend_data") || "{}";
      let data = {};
      try { data = JSON.parse(prior); } catch { data = {}; }
      data.slidesReviewed = true;
      window.scorm.set("cmi.suspend_data", JSON.stringify(data).slice(0, 4000));
      // Do not set lesson_status here unless this page is the SCO launch page.
      window.scorm.commit();
    }
    btnReviewed.textContent = "Marked as Reviewed ✓";
    btnReviewed.disabled = true;
  });
})();
