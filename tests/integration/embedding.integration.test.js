// Optional integration test. Requires network + model download. Skip in CI by default.
const EmbeddingService = require('../../web/demo/js/embedding-service.js');

const shouldRun = process.env.INTEGRATION_EMBEDDING === '1';
const describeFn = shouldRun ? describe : describe.skip;

// Note: This uses the real embedding service. It will download the model via CDN
// and may take several seconds on first run. Intended for manual verification.
describeFn('EmbeddingService integration (real model)', () => {
  jest.setTimeout(30000); // allow model download

  test('happy vs joyful similarity is reasonably high', async () => {
    const e1 = await EmbeddingService.embed('I feel very happy and joyful today.');
    const e2 = await EmbeddingService.embed('What a joyful, delightful feeling of happiness!');
    expect(e1).not.toBeNull();
    expect(e2).not.toBeNull();
    const sim = EmbeddingService.similarity(e1, e2);
    expect(sim).toBeGreaterThan(0.5); // looser threshold due to model variability
  });
});
