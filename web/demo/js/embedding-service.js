(function() {
"use strict";

/**
 * Embedding Service (browser-first with graceful fallbacks)
 *
 * - Lazily loads Xenova/all-MiniLM-L6-v2 via transformers.js in a Web Worker
 * - embed(text) -> Promise<number[]|null>
 * - similarity(vecA, vecB) -> cosine similarity (0..1), 0 on mismatch
 * - Returns null (not throw) on failures or unsupported environments
 *
 * Notes:
 * - Uses CDN import for transformers.js to avoid bundler requirements
 * - In non-worker environments (e.g., Jest/Node), embed() resolves to null
 */

// Inline worker script as a Blob to avoid extra files/paths.
// Loads transformers.js from CDN and caches the feature-extraction pipeline.
const WORKER_SOURCE = `
  self.importScripts('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.15.0/dist/transformers.min.js');
  let extractorPromise = null;
  async function getExtractor() {
    if (!extractorPromise) {
      extractorPromise = self.transformers.pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    }
    return extractorPromise;
  }
  self.onmessage = async (event) => {
    const { id, text } = event.data || {};
    if (!id) return;
    if (!text || typeof text !== 'string') {
      self.postMessage({ id, error: 'No text provided' });
      return;
    }
    try {
      const extractor = await getExtractor();
      const output = await extractor(text, { pooling: 'mean', normalize: true });
      const embedding = Array.from(output.data);
      self.postMessage({ id, embedding });
    } catch (err) {
      self.postMessage({ id, error: (err && err.message) || 'Embedding failed' });
    }
  };
`;

let worker = null;
let workerInitError = null;
const pending = new Map();
let nextId = 1;

const NODE_FALLBACK_ENABLED = typeof process !== 'undefined' && process.env && (process.env.INTEGRATION_EMBEDDING === '1' || process.env.EMBED_NODE === '1');
let nodeExtractorPromise = null;
let nodeExtractorError = null;

async function getNodeExtractor() {
  if (!NODE_FALLBACK_ENABLED) return null;
  if (!nodeExtractorPromise) {
    nodeExtractorPromise = (async () => {
      let mod = null;
      try {
        if (typeof require === 'function') {
          mod = require('@xenova/transformers');
        } else {
          mod = await import('@xenova/transformers');
        }
      } catch (primaryErr) {
        // Fallback to dynamic import if require failed, or vice versa
        try {
          mod = await import('@xenova/transformers');
        } catch (importErr) {
          throw importErr || primaryErr;
        }
      }
      const transformers = mod && mod.default ? mod.default : mod;
      if (!transformers || typeof transformers.pipeline !== 'function') {
        throw new Error('transformers pipeline not available');
      }
      return transformers.pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    })();
  }
  try {
    return await nodeExtractorPromise;
  } catch (err) {
    nodeExtractorError = err;
    return null;
  }
}

function ensureWorker() {
  if (worker || workerInitError) return;
  try {
    if (typeof Worker === 'undefined' || typeof Blob === 'undefined' || typeof URL === 'undefined') {
      workerInitError = new Error('Workers not supported in this environment');
      return;
    }
    const blob = new Blob([WORKER_SOURCE], { type: 'application/javascript' });
    const url = URL.createObjectURL(blob);
    worker = new Worker(url);
    worker.onmessage = (event) => {
      const { id, embedding, error } = event.data || {};
      const deferred = pending.get(id);
      if (!deferred) return;
      pending.delete(id);
      if (error) {
        deferred.reject(new Error(error));
        return;
      }
      deferred.resolve(embedding || null);
    };
    worker.onerror = (err) => {
      workerInitError = err instanceof Error ? err : new Error('Worker error');
      // Reject all pending requests
      pending.forEach((deferred) => deferred.reject(workerInitError));
      pending.clear();
    };
  } catch (err) {
    workerInitError = err instanceof Error ? err : new Error('Unable to start embedding worker');
  }
}

/**
 * Computes cosine similarity between two vectors. Returns 0 on mismatch/invalid input.
 * @param {Array<number>} a
 * @param {Array<number>} b
 * @returns {number}
 */
function similarity(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b) || a.length === 0 || b.length === 0 || a.length !== b.length) {
    return 0;
  }
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    const va = Number(a[i]);
    const vb = Number(b[i]);
    if (!Number.isFinite(va) || !Number.isFinite(vb)) return 0;
    dot += va * vb;
    normA += va * va;
    normB += vb * vb;
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * embed(text): Returns embedding or null (on failure/unsupported env).
 * @param {string} text
 * @returns {Promise<Array<number>|null>}
 */
async function embed(text) {
  if (!text || typeof text !== 'string') return null;

  // Primary path: Worker (browser-first)
  ensureWorker();
  if (worker && !workerInitError) {
    return new Promise((resolve, reject) => {
      const id = nextId++;
      pending.set(id, { resolve, reject });
      try {
        worker.postMessage({ id, text });
      } catch (err) {
        pending.delete(id);
        resolve(null);
      }
      // Safety timeout to avoid dangling promises (15s)
      setTimeout(() => {
        if (pending.has(id)) {
          pending.delete(id);
          resolve(null);
        }
      }, 15000);
    });
  }

  // Node fallback for integration/Node environments (opt-in)
  const extractor = await getNodeExtractor();
  if (!extractor) return null;
  try {
    const output = await extractor(text, { pooling: 'mean', normalize: true });
    if (output && output.data) return Array.from(output.data);
    if (output && Array.isArray(output)) return output;
    return null;
  } catch (err) {
    return null;
  }
}

const EmbeddingService = { embed, similarity, _nodeExtractorError: () => nodeExtractorError };

if (typeof module !== 'undefined' && module.exports) {
  module.exports = EmbeddingService;
}
if (typeof window !== 'undefined') {
  window.EmbeddingService = EmbeddingService;
}

})();
