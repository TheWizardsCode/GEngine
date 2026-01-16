/**
 * LLM Adapter (OpenAI)
 * 
 * Provider-agnostic adapter for making LLM API calls from the browser.
 * Supports OpenAI API with creativity mapping and timeout handling.
 * 
 * @module llm-adapter
 */
(function() {
"use strict";

/**
 * Default timeout in milliseconds
 * @const {number}
 */
const DEFAULT_TIMEOUT_MS = 5000;

/**
 * OpenAI API endpoint for chat completions
 * @const {string}
 */
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

/**
 * Default model to use
 * @const {string}
 */
const DEFAULT_MODEL = 'gpt-4o-mini';

/**
 * Maps creativity parameter (0.0-1.0) to OpenAI temperature (0.0-2.0)
 * 
 * @param {number} creativity - Creativity value between 0.0 and 1.0
 * @returns {number} Temperature value between 0.0 and 2.0
 */
function creativityToTemperature(creativity) {
  // Clamp creativity to valid range
  const clamped = Math.max(0, Math.min(1, creativity));
  // Map to temperature: 0.0-1.0 → 0.0-2.0
  return clamped * 2.0;
}

/**
 * Error types for LLM operations
 * @enum {string}
 */
const ErrorType = {
  TIMEOUT: 'timeout',
  NETWORK: 'network',
  API_ERROR: 'api_error',
  RATE_LIMIT: 'rate_limit',
  INVALID_KEY: 'invalid_key',
  PARSE_ERROR: 'parse_error',
  UNKNOWN: 'unknown'
};

/**
 * Creates an error result object
 * 
 * @param {string} type - Error type from ErrorType enum
 * @param {string} message - Human-readable error message
 * @param {Object} [details] - Additional error details
 * @returns {{error: true, type: string, message: string, details?: Object}}
 */
function createError(type, message, details = null) {
  const error = {
    error: true,
    type: type,
    message: message
  };
  if (details) {
    error.details = details;
  }
  return error;
}

/**
 * Parses JSON from LLM response, handling common issues
 * 
 * @param {string} text - Raw response text
 * @returns {{success: boolean, data?: Object, error?: string}}
 */
function parseJsonResponse(text) {
  if (!text || typeof text !== 'string') {
    return { success: false, error: 'Empty response' };
  }
  
  // Try direct parse first
  try {
    const data = JSON.parse(text);
    return { success: true, data };
  } catch (e) {
    // Continue to try extraction methods
  }
  
  // Try to extract JSON from markdown code blocks
  const codeBlockMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlockMatch) {
    try {
      const data = JSON.parse(codeBlockMatch[1].trim());
      return { success: true, data };
    } catch (e) {
      // Continue
    }
  }
  
  // Try to find JSON object in the text
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      const data = JSON.parse(jsonMatch[0]);
      return { success: true, data };
    } catch (e) {
      return { success: false, error: `Failed to parse extracted JSON: ${e.message}` };
    }
  }
  
  return { success: false, error: 'No valid JSON found in response' };
}

/**
 * Generates a branch proposal using the OpenAI API
 * 
 * @param {Object} options - Generation options
 * @param {string} options.systemPrompt - System prompt for the LLM
 * @param {string} options.userPrompt - User prompt with context
 * @param {string} options.apiKey - OpenAI API key
 * @param {number} [options.creativity=0.7] - Creativity level (0.0-1.0)
 * @param {number} [options.timeoutMs=5000] - Timeout in milliseconds
 * @param {string} [options.model] - Model to use (defaults to gpt-4o-mini)
 * @returns {Promise<Object>} The parsed proposal or error object
 */
async function generateProposal(options) {
  const {
    systemPrompt,
    userPrompt,
    apiKey,
    creativity = 0.7,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    model = DEFAULT_MODEL
  } = options;
  
  // Validate required parameters
  if (!apiKey) {
    return createError(ErrorType.INVALID_KEY, 'API key is required');
  }
  
  if (!systemPrompt || !userPrompt) {
    return createError(ErrorType.UNKNOWN, 'System and user prompts are required');
  }
  
  const temperature = creativityToTemperature(creativity);
  const startTime = Date.now();
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: temperature,
        max_tokens: 1000,
        response_format: { type: 'json_object' }
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    const generationTimeMs = Date.now() - startTime;
    
    // Handle HTTP errors
    if (!response.ok) {
      const errorBody = await response.text().catch(() => '');
      let errorDetails = {};
      try {
        errorDetails = JSON.parse(errorBody);
      } catch (e) {
        errorDetails = { raw: errorBody };
      }
      
      // Specific error types
      if (response.status === 401) {
        return createError(ErrorType.INVALID_KEY, 'Invalid API key', errorDetails);
      }
      if (response.status === 429) {
        return createError(ErrorType.RATE_LIMIT, 'Rate limit exceeded. Try again in a moment.', errorDetails);
      }
      if (response.status >= 500) {
        return createError(ErrorType.API_ERROR, 'OpenAI service error', errorDetails);
      }
      
      return createError(
        ErrorType.API_ERROR,
        `API error: ${response.status} ${response.statusText}`,
        errorDetails
      );
    }
    
    // Parse response
    const responseData = await response.json();
    
    if (!responseData.choices || !responseData.choices[0]?.message?.content) {
      return createError(ErrorType.PARSE_ERROR, 'Invalid response structure from API');
    }
    
    const content = responseData.choices[0].message.content;
    const parseResult = parseJsonResponse(content);
    
    if (!parseResult.success) {
      return createError(ErrorType.PARSE_ERROR, parseResult.error, { raw: content });
    }
    
    // Add generation metadata
    const proposal = parseResult.data;
    proposal._meta = {
      model: model,
      temperature: temperature,
      generation_time_ms: generationTimeMs,
      created_at: new Date().toISOString()
    };
    
    return proposal;
    
  } catch (e) {
    clearTimeout(timeoutId);
    
    if (e.name === 'AbortError') {
      return createError(ErrorType.TIMEOUT, `Request timed out after ${timeoutMs}ms`);
    }
    
    if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
      return createError(ErrorType.NETWORK, 'Network error. Check your connection.');
    }
    
    return createError(ErrorType.UNKNOWN, e.message);
  }
}

/**
 * Tests the API connection with a minimal request
 * 
 * @param {string} apiKey - OpenAI API key to test
 * @returns {Promise<{success: boolean, error?: string}>}
 */
async function testConnection(apiKey) {
  const result = await generateProposal({
    systemPrompt: 'You are a test assistant. Respond with valid JSON.',
    userPrompt: 'Return {"test": true}',
    apiKey: apiKey,
    creativity: 0,
    timeoutMs: 10000
  });
  
  if (result.error) {
    return { success: false, error: result.message };
  }
  
  return { success: true };
}

/**
 * Generates a unique proposal ID
 * 
 * @returns {string} UUID-like identifier
 */
function generateProposalId() {
  // Generate a UUID v4-like string
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Export for use in other modules
const LLMAdapter = {
  generateProposal,
  testConnection,
  creativityToTemperature,
  parseJsonResponse,
  generateProposalId,
  ErrorType,
  DEFAULT_TIMEOUT_MS,
  DEFAULT_MODEL,
  OPENAI_API_URL
};

// CommonJS export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LLMAdapter;
}

// Browser global export
if (typeof window !== 'undefined') {
  window.LLMAdapter = LLMAdapter;
}

})();
