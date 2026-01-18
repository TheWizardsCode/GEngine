(function() {
"use strict";

// Lightweight Director module implementing a 5-step decision pipeline.
// - validation (uses ProposalValidator.quickValidate)
// - return-path feasibility
// - risk scoring (3 active metrics + placeholders)
// - coherence check (simple threshold)
// - final decision + telemetry

// Node/browser performance shim
let perf;
try {
  perf = (typeof performance !== 'undefined') ? performance : require('perf_hooks').performance;
} catch (e) {
  perf = (typeof performance !== 'undefined') ? performance : { now: () => Date.now() };
}

function safeNumber(v, fallback = 0) {
  return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}

function clamp01(v, fallback = 0) {
  const n = safeNumber(v, fallback);
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
}

function generateUUID() {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
  } catch (e) {}
  // Fallback RFC4122-ish generator
  const rand = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
  return `uuid-${rand()}${rand()}-${rand()}-${rand()}-${rand()}-${rand()}${rand()}${rand()}`;
}

function buildDecisionMetrics(proposal = {}, context = {}) {
  const text = (proposal.content && typeof proposal.content.text === 'string') ? proposal.content.text : '';
  const confidence = clamp01(proposal.metadata && proposal.metadata.confidence_score, 0.5);
  const pacing = clamp01((text.length - 300) / 700, 0);
  const returnPath = clamp01(context.returnPathCheck && context.returnPathCheck.confidence, 0);
  return {
    confidence,
    pacing,
    returnPath,
    thematic: null,
    lore: null,
    voice: null
  };
}

/**
 * checkReturnPath(returnPath, story)
 * Minimal existence check: looks for named knots on the inkjs story object
 * Returns { feasible, reason, confidence }
 */
function checkReturnPath(returnPath, story, proposal = {}) {
  if (!returnPath) {
    return { feasible: false, reason: 'No return_path provided', confidence: 0.0 };
  }

  // Try inkjs internal named content if available
  try {
    const named = story && story.mainContentContainer && story.mainContentContainer._namedContent;
    if (named && typeof named === 'object') {
      if (Object.prototype.hasOwnProperty.call(named, returnPath)) {
        return { feasible: true, reason: 'Return path exists', confidence: 0.9 };
      }
      return { feasible: false, reason: 'Return path knot does not exist', confidence: 0.0 };
    }
  } catch (e) {
    // fallthrough to fallback check
  }

  // Fallback: if the proposal itself included a validReturnPaths array on generation we can trust that
  try {
    if (Array.isArray(proposal && proposal.validReturnPaths)) {
      if (proposal.validReturnPaths.includes(returnPath)) {
        return { feasible: true, reason: 'Return path listed in proposal.validReturnPaths', confidence: 0.9 };
      }
      return { feasible: false, reason: 'Return path not present in proposal.validReturnPaths', confidence: 0.0 };
    }
  } catch (e) {}

  // Secondary fallback: global validReturnPaths (legacy tests)
  try {
    if (Array.isArray(window && window.__proposalValidReturnPaths)) {
      if (window.__proposalValidReturnPaths.includes(returnPath)) {
        return { feasible: true, reason: 'Return path listed in validReturnPaths', confidence: 0.9 };
      }
      return { feasible: false, reason: 'Return path not present in validReturnPaths', confidence: 0.0 };
    }
  } catch (e) {}

  // Unknown story shape -> be conservative: reject (in production we might attempt reachability analysis)
  return { feasible: false, reason: 'Unable to verify return path', confidence: 0.0 };
}

/**
 * computeRiskScore(proposal, context, config)
 * Lightweight deterministic scoring using three active metrics and three placeholders.
 * Returns number between 0.0 (low risk) and 1.0 (high risk).
 */
function computeRiskScore(proposal = {}, context = {}, config = {}) {
  // We want deterministic results given same inputs
  const confidence = safeNumber(proposal.metadata && proposal.metadata.confidence_score, 0.5);
  // proposal_confidence_risk: high confidence -> low risk
  const proposal_confidence_risk = 1.0 - Math.max(0, Math.min(1, confidence));

  // narrative_pacing_risk: heuristic based on content length vs phase target
  const text = (proposal.content && proposal.content.text) || '';
  const len = text.length;
  const phase = (context && context.phase) || 'exposition';
  const defaultPacingTargets = Object.assign({
    exposition: 300,
    rising_action: 400,
    climax: 700,
    falling_action: 350,
    resolution: 300
  }, (config && config.pacingTargets) || {});
  const expectedLen = Math.max(1, safeNumber(defaultPacingTargets[phase], 300));
  const toleranceFactor = Math.max(0.05, safeNumber(config && config.pacingToleranceFactor, 0.6));
  // Risk grows once length exceeds expected; at expected*(1+toleranceFactor) risk reaches ~1
  const pacingRatio = len / expectedLen;
  const pacingOver = Math.max(0, pacingRatio - 1);
  const narrative_pacing_risk = Math.min(1, pacingOver / toleranceFactor);

  // return_path_confidence_risk derived from context.returnPathCheck (if present)
  const returnPathConfidence = safeNumber((context && context.returnPathCheck && context.returnPathCheck.confidence), 0.0);
  const return_path_confidence_risk = 1.0 - Math.max(0, Math.min(1, returnPathConfidence));

  // Placeholder metrics (thematic, lore, voice)
  const placeholder = safeNumber(config.placeholderDefault, 0.3);
  const thematic_consistency_risk = placeholder;
  const lore_adherence_risk = placeholder;
  const character_voice_risk = placeholder;

  // Weights (configurable)
  const weights = Object.assign({
    proposal_confidence: 0.75,
    narrative_pacing: 0.15,
    return_path_confidence: 0.1,
    thematic_consistency: 0,
    lore_adherence: 0,
    character_voice: 0
  }, config.weights || {});

  // Weighted average of active metrics
  const activeSum = weights.proposal_confidence + weights.narrative_pacing + weights.return_path_confidence;
  const activeScore = (
    proposal_confidence_risk * weights.proposal_confidence +
    narrative_pacing_risk * weights.narrative_pacing +
    return_path_confidence_risk * weights.return_path_confidence
  ) / Math.max(1e-6, activeSum);

  // Add fraction for placeholders (kept small / configurable)
  const placeholderSum = (weights.thematic_consistency || 0) + (weights.lore_adherence || 0) + (weights.character_voice || 0);
  const placeholderScore = (thematic_consistency_risk * (weights.thematic_consistency || 0) +
                           lore_adherence_risk * (weights.lore_adherence || 0) +
                           character_voice_risk * (weights.character_voice || 0)) / Math.max(1e-6, placeholderSum || 1);

  // Mix active + placeholder (placeholder usually zero in defaults)
  const totalWeight = activeSum + placeholderSum;
  const totalScore = (activeScore * activeSum + placeholderScore * placeholderSum) / Math.max(1e-6, totalWeight);

  // Clamp
  return Math.max(0, Math.min(1, totalScore));
}

/**
 * emitDecisionTelemetry(decisionResult, extras)
 * Emits director_decision events via Telemetry (if available) and buffers last 50 in sessionStorage.
 */
function emitDecisionTelemetry(decisionResult = {}, extras = {}) {
  const proposalId = decisionResult.proposal_id || (decisionResult.proposal && decisionResult.proposal.id);
  const writerMs = safeNumber(decisionResult.writerMs ?? extras.writerMs, 0);
  const directorMs = safeNumber(decisionResult.directorMs ?? decisionResult.latencyMs ?? extras.directorMs, 0);
  const totalMs = safeNumber(decisionResult.totalMs ?? (writerMs + directorMs), writerMs + directorMs);

  const payload = Object.assign({}, decisionResult, {
    proposal_id: proposalId || generateUUID(),
    timestamp: new Date().toISOString(),
    writerMs,
    directorMs,
    totalMs,
    metrics: Object.assign({
      confidence: null,
      pacing: null,
      returnPath: null,
      thematic: null,
      lore: null,
      voice: null
    }, decisionResult.metrics || extras.metrics || {})
  });

  // Ensure required fields exist even if undefined
  const eventName = 'director_decision';

  try {
    if (typeof window !== 'undefined' && window.Telemetry && typeof window.Telemetry.emit === 'function') {
      window.Telemetry.emit(eventName, payload);
    } else if (typeof console !== 'undefined') {
      console.log('[director] telemetry', payload);
    }

    // Buffer in sessionStorage
    if (typeof sessionStorage !== 'undefined') {
      try {
        const raw = sessionStorage.getItem('ge-hch.director.telemetry') || '[]';
        const arr = JSON.parse(raw);
        arr.push(payload);
        while (arr.length > 50) arr.shift();
        sessionStorage.setItem('ge-hch.director.telemetry', JSON.stringify(arr));
      } catch (e) {}
    }
  } catch (e) {}

  return payload;
}

/**
 * evaluate(proposal, storyContext, config)
 * Main entry point. Returns { decision, reason, riskScore, latencyMs }
 */
async function evaluate(proposal, storyContext = {}, config = {}) {
  const start = perf.now();

  // Quick sanity
  if (!proposal || typeof proposal !== 'object') {
    throw new Error('Malformed proposal');
  }

  // Step 1: validation (schema + quick safety)
  try {
    const validation = (typeof ProposalValidator !== 'undefined' && ProposalValidator.quickValidate)
      ? ProposalValidator.quickValidate(proposal)
      : { valid: true };

    if (!validation || !validation.valid) {
      const latencyMs = Math.max(0, perf.now() - start);
      const result = { decision: 'reject', reason: validation && validation.reason ? validation.reason : 'Failed policy validation', riskScore: 1.0, latencyMs, writerMs: 0, directorMs: latencyMs, totalMs: latencyMs };
      emitDecisionTelemetry(result);
      return result;
    }
  } catch (e) {
    const latencyMs = Math.max(0, perf.now() - start);
    const result = { decision: 'reject', reason: 'Validation error', riskScore: 1.0, latencyMs, writerMs: 0, directorMs: latencyMs, totalMs: latencyMs };
    emitDecisionTelemetry(result);
    return result;
  }

  // Step 2: return-path feasibility
  let returnCheck = { feasible: true, reason: 'No check performed', confidence: 0.9 };
  try {
    const returnPath = (proposal.content && proposal.content.return_path) || null;
    returnCheck = checkReturnPath(returnPath, storyContext && storyContext.story, proposal);
    if (!returnCheck.feasible) {
    const latencyMs = Math.max(0, perf.now() - start);
    const result = { decision: 'reject', reason: `Return path check failed: ${returnCheck.reason}`, riskScore: 1.0, latencyMs, writerMs: 0, directorMs: latencyMs, totalMs: latencyMs };
    emitDecisionTelemetry(result);
    return result;
  }
} catch (e) {
  // conservative rejection
  const latencyMs = Math.max(0, perf.now() - start);
  const result = { decision: 'reject', reason: 'Return path check error', riskScore: 1.0, latencyMs, writerMs: 0, directorMs: latencyMs, totalMs: latencyMs };
  emitDecisionTelemetry(result);
  return result;
}


  // Step 3: risk scoring
  const context = { returnPathCheck: returnCheck, story: storyContext && storyContext.story };
  const riskScore = computeRiskScore(proposal, context, config);

  // Step 4: coherence check (threshold)
  const threshold = safeNumber((config && config.riskThreshold), 0.4);
  const decision = (riskScore <= threshold) ? 'approve' : 'reject';
  const reason = decision === 'approve' ? 'Risk acceptable' : 'Risk above threshold';

  const latencyMs = Math.max(0, perf.now() - start);
  const writerMs = safeNumber(config && config.writerMs, 0);
  const directorMs = latencyMs;
  const totalMs = writerMs + directorMs;
  const metrics = buildDecisionMetrics(proposal, context);
  const result = {
    proposal_id: proposal.id || proposal.proposal_id,
    decision,
    reason,
    riskScore,
    latencyMs,
    writerMs,
    directorMs,
    totalMs,
    metrics
  };

  emitDecisionTelemetry(result);
  return result;
}

// Exports
const Director = {
  evaluate,
  checkReturnPath,
  computeRiskScore,
  emitDecisionTelemetry
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = Director;
}
if (typeof window !== 'undefined') {
  window.Director = Director;
}

})();
