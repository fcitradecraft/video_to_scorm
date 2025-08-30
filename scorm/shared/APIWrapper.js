(function (global) {
  var api = null, initialized = false, findTries = 0;

  function findAPI(win) {
    while (!win.API && win.parent && win.parent !== win) {
      findTries++; if (findTries > 500) break;
      win = win.parent;
    }
    return win.API || null;
  }

  function getAPI() {
    if (api) return api;
    api = findAPI(window) || (window.opener ? findAPI(window.opener) : null);
    return api;
  }

  var scorm = {
    init: function () {
      var A = getAPI();
      if (!A) return false;
      if (initialized) return true;
      initialized = (A.LMSInitialize("") + "" === "true");
      return initialized;
    },
    get: function (el) {
      var A = getAPI(); if (!A) return "";
      var v = A.LMSGetValue(el);
      return v == "undefined" || v == null ? "" : v;
    },
    set: function (el, val) {
      var A = getAPI(); if (!A) return false;
      return (A.LMSSetValue(el, String(val)) + "" === "true");
    },
    commit: function () {
      var A = getAPI(); if (!A) return false;
      return (A.LMSCommit("") + "" === "true");
    },
    finish: function () {
      var A = getAPI(); if (!A) return false;
      var ok = (A.LMSFinish("") + "" === "true");
      initialized = false; return ok;
    }
  };

  global.scorm = scorm;
})(window);
