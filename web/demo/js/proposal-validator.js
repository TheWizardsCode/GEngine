/**
 * Proposal Validator
 * 
 * Validates AI-generated branch proposals against schema and safety rules.
 * Performs schema conformance check and basic profanity filtering.
 * 
 * @module proposal-validator
 */
(function() {
"use strict";

/**
 * Basic profanity word list for content filtering
 * This is a minimal list for demonstration; production should use a more comprehensive list
 * @const {string[]}
 */
const PROFANITY_LIST = [
  // Common profanity (intentionally minimal for demo)
  'fuck', 'shit', 'damn', 'ass', 'bitch', 'bastard', 'crap',
  // Slurs and hate speech indicators
  'nigger', 'faggot', 'retard', 'cunt',
  // Violence indicators
  'kill yourself', 'suicide', 'murder',
  // Explicit content indicators
  'porn', 'xxx', 'nude', 'naked'
];

/**
 * Schema requirements for a valid branch proposal
 * Based on docs/dev/m2-schemas/branch-proposal.json (simplified for inline use)
 */
const REQUIRED_FIELDS = {
  'choice_text': 'string',
  'content': 'object',
  'content.text': 'string',
  'content.return_path': 'string'
};

/**
 * Optional fields with their expected types
 */
const OPTIONAL_FIELDS = {
  'content.branch_type': 'string',
  'metadata': 'object',
  'metadata.confidence_score': 'number',
  'metadata.thematic_fit': 'number'
};

/**
 * Maximum allowed lengths
 */
const MAX_LENGTHS = {
  choice_text: 100,
  content_text: 2000,
  return_path: 50
};

/**
 * Validation result type
 * @typedef {Object} ValidationResult
 * @property {boolean} valid - Whether the proposal passes validation
 * @property {string[]} errors - Array of error messages
 * @property {string[]} warnings - Array of warning messages
 */

/**
 * Gets a nested property value from an object using dot notation
 * 
 * @param {Object} obj - Object to query
 * @param {string} path - Dot-notation path (e.g., 'content.text')
 * @returns {*} The value at the path or undefined
 */
function getNestedValue(obj, path) {
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined;
  }, obj);
}

/**
 * Checks if text contains profanity (case-insensitive)
 * 
 * @param {string} text - Text to check
 * @returns {{hasProfanity: boolean, matches: string[]}}
 */
function checkProfanity(text) {
  if (!text || typeof text !== 'string') {
    return { hasProfanity: false, matches: [] };
  }
  
  const lowerText = text.toLowerCase();
  const matches = [];
  
  for (const word of PROFANITY_LIST) {
    // Use word boundary checking for single words, direct check for phrases
    if (word.includes(' ')) {
      if (lowerText.includes(word)) {
        matches.push(word);
      }
    } else {
      // Match whole words only using regex
      const regex = new RegExp(`\\b${word}\\b`, 'i');
      if (regex.test(lowerText)) {
        matches.push(word);
      }
    }
  }
  
  return {
    hasProfanity: matches.length > 0,
    matches: matches
  };
}

/**
 * Validates a proposal against the schema requirements
 * 
 * @param {Object} proposal - The proposal to validate
 * @returns {ValidationResult}
 */
function validateSchema(proposal) {
  const errors = [];
  const warnings = [];
  
  if (!proposal || typeof proposal !== 'object') {
    return {
      valid: false,
      errors: ['Proposal must be an object'],
      warnings: []
    };
  }
  
  // Check required fields
  for (const [path, expectedType] of Object.entries(REQUIRED_FIELDS)) {
    const value = getNestedValue(proposal, path);
    
    if (value === undefined || value === null) {
      errors.push(`Missing required field: ${path}`);
    } else if (typeof value !== expectedType) {
      errors.push(`Field ${path} must be ${expectedType}, got ${typeof value}`);
    }
  }
  
  // Check optional fields if present
  for (const [path, expectedType] of Object.entries(OPTIONAL_FIELDS)) {
    const value = getNestedValue(proposal, path);
    
    if (value !== undefined && value !== null && typeof value !== expectedType) {
      warnings.push(`Field ${path} should be ${expectedType}, got ${typeof value}`);
    }
  }
  
  // Check length constraints
  if (proposal.choice_text && proposal.choice_text.length > MAX_LENGTHS.choice_text) {
    warnings.push(`choice_text exceeds recommended length (${proposal.choice_text.length} > ${MAX_LENGTHS.choice_text})`);
  }
  
  if (proposal.content?.text && proposal.content.text.length > MAX_LENGTHS.content_text) {
    errors.push(`content.text exceeds maximum length (${proposal.content.text.length} > ${MAX_LENGTHS.content_text})`);
  }
  
  if (proposal.content?.return_path && proposal.content.return_path.length > MAX_LENGTHS.return_path) {
    errors.push(`content.return_path exceeds maximum length`);
  }
  
  // Validate confidence scores are in range
  if (proposal.metadata?.confidence_score !== undefined) {
    const score = proposal.metadata.confidence_score;
    if (score < 0 || score > 1) {
      warnings.push(`confidence_score should be between 0.0 and 1.0, got ${score}`);
    }
  }
  
  if (proposal.metadata?.thematic_fit !== undefined) {
    const score = proposal.metadata.thematic_fit;
    if (score < 0 || score > 1) {
      warnings.push(`thematic_fit should be between 0.0 and 1.0, got ${score}`);
    }
  }
  
  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: warnings
  };
}

/**
 * Validates proposal content for profanity and unsafe content
 * 
 * @param {Object} proposal - The proposal to validate
 * @returns {ValidationResult}
 */
function validateContent(proposal) {
  const errors = [];
  const warnings = [];
  
  if (!proposal) {
    return { valid: false, errors: ['No proposal provided'], warnings: [] };
  }
  
  // Check choice text for profanity
  if (proposal.choice_text) {
    const result = checkProfanity(proposal.choice_text);
    if (result.hasProfanity) {
      errors.push(`Profanity detected in choice_text`);
    }
  }
  
  // Check content text for profanity
  if (proposal.content?.text) {
    const result = checkProfanity(proposal.content.text);
    if (result.hasProfanity) {
      errors.push(`Profanity detected in content.text`);
    }
  }
  
  // Check for empty/meaningless content
  if (proposal.content?.text && proposal.content.text.trim().length < 20) {
    warnings.push('Content text is very short; may not provide meaningful narrative');
  }
  
  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: warnings
  };
}

/**
 * Validates that the return path is in the list of valid targets
 * 
 * @param {Object} proposal - The proposal to validate
 * @param {string[]} validReturnPaths - Array of valid return path knot names
 * @returns {ValidationResult}
 */
function validateReturnPath(proposal, validReturnPaths) {
  const errors = [];
  const warnings = [];
  
  if (!proposal?.content?.return_path) {
    errors.push('No return_path specified');
    return { valid: false, errors, warnings };
  }
  
  const returnPath = proposal.content.return_path;
  
  // Check if return path is valid
  if (validReturnPaths && validReturnPaths.length > 0) {
    if (!validReturnPaths.includes(returnPath)) {
      warnings.push(`Return path "${returnPath}" is not in the recommended list. May cause navigation issues.`);
      console.warn(`[proposal-validator] Return path "${returnPath}" not in valid paths:`, validReturnPaths);
    }
  }
  
  // Check for ending paths (should not be return targets)
  const endingPaths = ['rescue_end', 'waiting_end', 'quiet_end', 'lost_end', 
                       'tower_gathering_end', 'urgent_return_end', 'revelation_end'];
  if (endingPaths.includes(returnPath)) {
    errors.push(`Return path "${returnPath}" is an ending - cannot use as return target`);
  }
  
  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: warnings
  };
}

/**
 * Performs full validation of a branch proposal
 * 
 * @param {Object} proposal - The proposal to validate
 * @param {Object} [options] - Validation options
 * @param {string[]} [options.validReturnPaths] - Array of valid return path knot names
 * @returns {ValidationResult}
 */
function validateProposal(proposal, options = {}) {
  const allErrors = [];
  const allWarnings = [];
  
  // Schema validation
  const schemaResult = validateSchema(proposal);
  allErrors.push(...schemaResult.errors);
  allWarnings.push(...schemaResult.warnings);
  
  // Content/safety validation
  const contentResult = validateContent(proposal);
  allErrors.push(...contentResult.errors);
  allWarnings.push(...contentResult.warnings);
  
  // Return path validation
  if (options.validReturnPaths) {
    const returnResult = validateReturnPath(proposal, options.validReturnPaths);
    allErrors.push(...returnResult.errors);
    allWarnings.push(...returnResult.warnings);
  }
  
  return {
    valid: allErrors.length === 0,
    errors: allErrors,
    warnings: allWarnings
  };
}

/**
 * Quick validation for real-time use (schema + profanity only)
 * Designed to complete in <50ms
 * 
 * @param {Object} proposal - The proposal to validate
 * @returns {{valid: boolean, reason?: string}}
 */
function quickValidate(proposal) {
  // Basic structure check
  if (!proposal || typeof proposal !== 'object') {
    return { valid: false, reason: 'Invalid proposal structure' };
  }
  
  if (!proposal.choice_text || typeof proposal.choice_text !== 'string') {
    return { valid: false, reason: 'Missing or invalid choice_text' };
  }
  
  if (!proposal.content?.text || typeof proposal.content.text !== 'string') {
    return { valid: false, reason: 'Missing or invalid content.text' };
  }
  
  if (!proposal.content?.return_path || typeof proposal.content.return_path !== 'string') {
    return { valid: false, reason: 'Missing or invalid return_path' };
  }
  
  // Quick profanity check
  const choiceCheck = checkProfanity(proposal.choice_text);
  if (choiceCheck.hasProfanity) {
    return { valid: false, reason: 'Content blocked by safety filter' };
  }
  
  const textCheck = checkProfanity(proposal.content.text);
  if (textCheck.hasProfanity) {
    return { valid: false, reason: 'Content blocked by safety filter' };
  }
  
  return { valid: true };
}

// Export for use in other modules
const ProposalValidator = {
  validateProposal,
  validateSchema,
  validateContent,
  validateReturnPath,
  quickValidate,
  checkProfanity,
  PROFANITY_LIST,
  MAX_LENGTHS
};

// CommonJS export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProposalValidator;
}

// Browser global export
if (typeof window !== 'undefined') {
  window.ProposalValidator = ProposalValidator;
}

})();
