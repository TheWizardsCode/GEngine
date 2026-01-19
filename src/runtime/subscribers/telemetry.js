// Telemetry subscriber for runtime HookManager
// Emits console-based telemetry events; in prod this should hook into telemetry module

module.exports = function createTelemetrySubscriber(telemetry = console) {
  return {
    name: 'runtime-telemetry-subscriber',
    async pre_inject(payload) {
      try {
        telemetry.log('telemetry.event', { event: 'pre_inject', payload });
      } catch (err) {
        // swallow
      }
    },
    async post_inject(payload) {
      try {
        telemetry.log('telemetry.event', { event: 'post_inject', payload });
      } catch (err) {}
    },
    async pre_checkpoint(payload) {
      try {
        telemetry.log('telemetry.event', { event: 'pre_checkpoint', payload });
      } catch (err) {}
    },
    async post_checkpoint(payload) {
      try {
        telemetry.log('telemetry.event', { event: 'post_checkpoint', payload });
      } catch (err) {}
    }
  };
};
