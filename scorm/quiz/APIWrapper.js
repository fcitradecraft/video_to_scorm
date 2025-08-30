// quiz/APIWrapper.js
// Prefer the shared helper. This shim ensures window.scorm exists.

(function () {
  // If the shared helper is already loaded, we're done.
  if (window.scorm) return;

  // Try to load the shared helper dynamically (works in many LMSes)
  var s = document.createElement('script');
  s.src = "../shared/APIWrapper.js";
  s.onload = function () {
    if (!window.scorm) {
      // ultra-minimal no-op fallback to avoid runtime errors during local testing
      window.scorm = {
        init: function(){ return false; },
        get: function(){ return ""; },
        set: function(){ return false; },
        commit: function(){ return false; },
        finish: function(){ return false; }
      };
      console.warn("Shared SCORM APIWrapper not found; using no-op fallback for local testing.");
    }
  };
  s.onerror = s.onload; // same fallback on error
  document.head.appendChild(s);
})();
