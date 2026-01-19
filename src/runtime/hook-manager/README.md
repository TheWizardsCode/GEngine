Runtime HookManager

Usage snippets (demo):

const HookManager = require('../hook-manager');
const createTelemetrySubscriber = require('../subscribers/telemetry');
const createPersistenceSubscriber = require('../subscribers/persistence');

const hm = new HookManager();
const telemetry = createTelemetrySubscriber(console);
const persistence = createPersistenceSubscriber();

// register handlers
hm.on('pre_inject', telemetry.pre_inject);
hm.on('post_inject', telemetry.post_inject);
hm.on('pre_checkpoint', telemetry.pre_checkpoint);
hm.on('post_checkpoint', telemetry.post_checkpoint);

hm.on('state_change', persistence.on_state_change);
hm.on('audit', persistence.audit);

// emit example
await hm.emitParallel('pre_inject', { branchId: 'b1' });

Note: subscribers must be resilient; HookManager will catch and surface handler results without throwing.
