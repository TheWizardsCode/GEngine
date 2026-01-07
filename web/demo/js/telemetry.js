(function () {
  "use strict";

  const Telemetry = {
    enabled: true,
    enable() {
      this.enabled = true;
    },
    disable() {
      this.enabled = false;
    },
    emit(eventName, payload) {
      if (!this.enabled) return;
      try {
        if (payload !== undefined) {
          console.log(eventName, payload);
        } else {
          console.log(eventName);
        }
      } catch (_) {
        // ignore console errors
      }
    },
  };

  if (typeof window !== 'undefined') {
    window.Telemetry = window.Telemetry || Telemetry;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Telemetry;
  }
})();
