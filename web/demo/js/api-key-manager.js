/**
 * API Key Management
 * 
 * Manages OpenAI API key storage, retrieval, and UI for the AI Writer.
 * Keys are stored in localStorage and prompted on first use.
 * 
 * @module api-key-manager
 */
(function() {
"use strict";

/**
 * localStorage key for storing the API key
 * @const {string}
 */
const STORAGE_KEY = 'ge-ai-writer-api-key';

/**
 * localStorage key for AI Writer settings
 * @const {string}
 */
const SETTINGS_KEY = 'ge-ai-writer-settings';

/**
 * Pattern for validating OpenAI API key format
 * Supports both old (sk-...) and new (sk-proj-...) formats
 * @const {RegExp}
 */
const API_KEY_PATTERN = /^sk-[a-zA-Z0-9_-]{20,}$/;

/**
 * Validates a URL format for API endpoints
 * 
 * @param {string} url - The URL to validate
 * @returns {{valid: boolean, reason?: string}} Validation result
 */
function validateEndpointUrl(url) {
  if (!url || typeof url !== 'string') {
    return { valid: false, reason: 'Endpoint URL is required' };
  }
  
  const trimmedUrl = url.trim();
  
  try {
    const parsed = new URL(trimmedUrl);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return { valid: false, reason: 'URL must use http or https protocol' };
    }
    return { valid: true };
  } catch (e) {
    return { valid: false, reason: 'Invalid URL format' };
  }
}

/**
 * Default settings for the AI Writer
 * @const {Object}
 */
const DEFAULT_SETTINGS = {
  enabled: true,
  creativity: 0.7,
  aiChoiceStyle: 'distinct', // 'normal' or 'distinct'
  showLoadingIndicator: true,
  apiEndpoint: 'https://api.openai.com/v1/chat/completions', // OpenAI-compatible endpoint
  useJsonMode: true // Some endpoints don't support response_format: { type: 'json_object' }
};

/**
 * Validates an API key format
 * 
 * @param {string} key - The API key to validate
 * @returns {{valid: boolean, reason?: string}} Validation result
 */
function validateKeyFormat(key) {
  if (!key || typeof key !== 'string') {
    return { valid: false, reason: 'API key is required' };
  }
  
  const trimmedKey = key.trim();
  
  if (!trimmedKey.startsWith('sk-')) {
    return { valid: false, reason: 'API key should start with "sk-"' };
  }
  
  if (trimmedKey.length < 20) {
    return { valid: false, reason: 'API key appears too short' };
  }
  
  if (!API_KEY_PATTERN.test(trimmedKey)) {
    return { valid: false, reason: 'API key format is invalid' };
  }
  
  return { valid: true };
}

/**
 * Gets the stored API key
 * 
 * @returns {string|null} The API key or null if not set
 */
function getApiKey() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch (e) {
    console.error('[api-key-manager] Failed to read API key from localStorage', e);
    return null;
  }
}

/**
 * Stores the API key in localStorage
 * 
 * @param {string} key - The API key to store
 * @returns {{success: boolean, reason?: string}} Result of the operation
 */
function setApiKey(key) {
  const validation = validateKeyFormat(key);
  if (!validation.valid) {
    return { success: false, reason: validation.reason };
  }
  
  try {
    localStorage.setItem(STORAGE_KEY, key.trim());
    return { success: true };
  } catch (e) {
    console.error('[api-key-manager] Failed to save API key to localStorage', e);
    return { success: false, reason: 'Failed to save key to storage' };
  }
}

/**
 * Clears the stored API key
 * 
 * @returns {boolean} True if successful
 */
function clearApiKey() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (e) {
    console.error('[api-key-manager] Failed to clear API key', e);
    return false;
  }
}

/**
 * Checks if an API key is stored
 * 
 * @returns {boolean} True if a key is stored
 */
function hasApiKey() {
  return getApiKey() !== null;
}

/**
 * Gets the current API endpoint URL from settings
 * 
 * @returns {string} The endpoint URL (defaults to OpenAI)
 */
function getEndpointUrl() {
  const settings = getSettings();
  return settings.apiEndpoint || DEFAULT_SETTINGS.apiEndpoint;
}

/**
 * Sets the API endpoint URL in settings
 * 
 * @param {string} url - The endpoint URL to set
 * @returns {{success: boolean, reason?: string}} Result of the operation
 */
function setEndpointUrl(url) {
  const validation = validateEndpointUrl(url);
  if (!validation.valid) {
    return { success: false, reason: validation.reason };
  }
  
  const result = saveSettings({ apiEndpoint: url.trim() });
  return result ? { success: true } : { success: false, reason: 'Failed to save settings' };
}

/**
 * Checks if JSON mode is enabled for the current endpoint
 * 
 * @returns {boolean} True if JSON mode is enabled
 */
function isJsonModeEnabled() {
  const settings = getSettings();
  return settings.useJsonMode !== false; // Default to true
}

/**
 * Gets the current AI Writer settings
 * 
 * @returns {Object} Settings object with defaults applied
 */
function getSettings() {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.error('[api-key-manager] Failed to read settings', e);
  }
  return { ...DEFAULT_SETTINGS };
}

/**
 * Saves AI Writer settings
 * 
 * @param {Object} settings - Settings to save (merged with existing)
 * @returns {boolean} True if successful
 */
function saveSettings(settings) {
  try {
    const current = getSettings();
    const merged = { ...current, ...settings };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
    return true;
  } catch (e) {
    console.error('[api-key-manager] Failed to save settings', e);
    return false;
  }
}

/**
 * Masks an API key for display (shows only last 4 characters)
 * 
 * @param {string} key - The API key to mask
 * @returns {string} Masked key like "sk-...xxxx"
 */
function maskApiKey(key) {
  if (!key || key.length < 8) {
    return '(invalid key)';
  }
  return `sk-...${key.slice(-4)}`;
}

// ============================================================================
// UI Components
// ============================================================================

/**
 * Creates and shows the API key modal
 * Returns a promise that resolves when a valid key is entered
 * 
 * @param {Object} options - Modal options
 * @param {boolean} options.allowCancel - Whether to show cancel button
 * @param {string} options.title - Modal title
 * @returns {Promise<string|null>} The entered API key or null if cancelled
 */
function showKeyModal(options = {}) {
  const { allowCancel = true, title = 'Enter OpenAI API Key' } = options;
  
  return new Promise((resolve) => {
    // Remove any existing modal
    const existingModal = document.getElementById('ai-key-modal');
    if (existingModal) {
      existingModal.remove();
    }
    
    // Create modal HTML
    const modal = document.createElement('div');
    modal.id = 'ai-key-modal';
    modal.className = 'ai-modal-overlay';
    modal.innerHTML = `
      <div class="ai-modal">
        <h2 class="ai-modal-title">${title}</h2>
        <p class="ai-modal-desc">
          To use AI-generated story branches, enter your OpenAI API key.
          Your key is stored locally in your browser.
        </p>
        <input 
          type="password" 
          id="ai-key-input" 
          class="ai-key-input" 
          placeholder="sk-..."
          autocomplete="off"
        />
        <div id="ai-key-error" class="ai-key-error" style="display: none;"></div>
        <div class="ai-modal-buttons">
          ${allowCancel ? '<button id="ai-key-cancel" class="ai-btn ai-btn-secondary">Cancel</button>' : ''}
          <button id="ai-key-save" class="ai-btn ai-btn-primary">Save Key</button>
        </div>
        <p class="ai-modal-note">
          Get an API key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">platform.openai.com</a>
        </p>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    const input = document.getElementById('ai-key-input');
    const errorEl = document.getElementById('ai-key-error');
    const saveBtn = document.getElementById('ai-key-save');
    const cancelBtn = document.getElementById('ai-key-cancel');
    
    // Focus input
    setTimeout(() => input.focus(), 100);
    
    function showError(message) {
      errorEl.textContent = message;
      errorEl.style.display = 'block';
      input.classList.add('ai-key-input-error');
    }
    
    function hideError() {
      errorEl.style.display = 'none';
      input.classList.remove('ai-key-input-error');
    }
    
    function handleSave() {
      hideError();
      const key = input.value;
      const validation = validateKeyFormat(key);
      
      if (!validation.valid) {
        showError(validation.reason);
        return;
      }
      
      const result = setApiKey(key);
      if (!result.success) {
        showError(result.reason);
        return;
      }
      
      modal.remove();
      resolve(key.trim());
    }
    
    function handleCancel() {
      modal.remove();
      resolve(null);
    }
    
    // Event listeners
    saveBtn.addEventListener('click', handleSave);
    if (cancelBtn) {
      cancelBtn.addEventListener('click', handleCancel);
    }
    
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        handleSave();
      } else if (e.key === 'Escape' && allowCancel) {
        handleCancel();
      }
    });
    
    input.addEventListener('input', hideError);
    
    // Click outside to cancel (if allowed)
    modal.addEventListener('click', (e) => {
      if (e.target === modal && allowCancel) {
        handleCancel();
      }
    });
  });
}

/**
 * Creates the AI Settings button and panel
 * Should be called once on page load
 */
function initSettingsUI() {
  // Don't init if already present
  if (document.getElementById('ai-settings-btn')) {
    return;
  }
  
  // Find the header controls area
  const controls = document.querySelector('header .controls');
  if (!controls) {
    console.warn('[api-key-manager] Could not find header controls for settings button');
    return;
  }
  
  // Create settings button
  const settingsBtn = document.createElement('button');
  settingsBtn.id = 'ai-settings-btn';
  settingsBtn.type = 'button';
  settingsBtn.textContent = 'AI Settings';
  settingsBtn.addEventListener('click', showSettingsPanel);
  
  // Insert before the tags span
  const tagsEl = document.getElementById('tags');
  if (tagsEl) {
    controls.insertBefore(settingsBtn, tagsEl);
  } else {
    controls.appendChild(settingsBtn);
  }
}

/**
 * Shows the AI settings panel
 */
function showSettingsPanel() {
  // Remove any existing panel
  const existingPanel = document.getElementById('ai-settings-panel');
  if (existingPanel) {
    existingPanel.remove();
    return; // Toggle behavior
  }
  
  const settings = getSettings();
  const hasKey = hasApiKey();
  const maskedKey = hasKey ? maskApiKey(getApiKey()) : 'Not set';
  const currentEndpoint = settings.apiEndpoint || DEFAULT_SETTINGS.apiEndpoint;
  const isDefaultEndpoint = currentEndpoint === DEFAULT_SETTINGS.apiEndpoint;
  
  const panel = document.createElement('div');
  panel.id = 'ai-settings-panel';
  panel.className = 'ai-settings-panel';
  panel.innerHTML = `
    <h3>AI Writer Settings</h3>
    
    <div class="ai-setting-row">
      <label>
        <input type="checkbox" id="ai-enabled" ${settings.enabled ? 'checked' : ''} />
        Enable AI-generated choices
      </label>
    </div>
    
    <div class="ai-setting-row">
      <label>API Key: <span class="ai-key-display">${maskedKey}</span></label>
      <button id="ai-update-key" class="ai-btn ai-btn-small">${hasKey ? 'Update' : 'Set Key'}</button>
      ${hasKey ? '<button id="ai-clear-key" class="ai-btn ai-btn-small ai-btn-danger">Clear</button>' : ''}
    </div>
    
    <div class="ai-setting-row ai-setting-endpoint">
      <label>
        API Endpoint:
        <input type="text" id="ai-endpoint-url" class="ai-endpoint-input" 
               value="${currentEndpoint}" 
               placeholder="https://api.openai.com/v1/chat/completions" />
      </label>
      <div class="ai-endpoint-hint">
        ${isDefaultEndpoint ? 'OpenAI (default)' : 'Custom endpoint'}
        ${!isDefaultEndpoint ? '<button id="ai-reset-endpoint" class="ai-btn ai-btn-small">Reset</button>' : ''}
      </div>
      <div id="ai-endpoint-error" class="ai-key-error" style="display: none;"></div>
    </div>
    
    <div class="ai-setting-row">
      <label>
        <input type="checkbox" id="ai-json-mode" ${settings.useJsonMode !== false ? 'checked' : ''} />
        Use JSON response mode
        <span class="ai-setting-hint">(disable for Ollama/older models)</span>
      </label>
    </div>
    
    <div class="ai-setting-row">
      <label>
        AI Choice Style:
        <select id="ai-choice-style">
          <option value="distinct" ${settings.aiChoiceStyle === 'distinct' ? 'selected' : ''}>Distinct (highlighted)</option>
          <option value="normal" ${settings.aiChoiceStyle === 'normal' ? 'selected' : ''}>Normal (blends in)</option>
        </select>
      </label>
    </div>
    
    <div class="ai-setting-row">
      <label>
        <input type="checkbox" id="ai-loading-indicator" ${settings.showLoadingIndicator ? 'checked' : ''} />
        Show loading indicator
      </label>
    </div>
    
    <div class="ai-setting-row">
      <label>
        Creativity: <span id="creativity-value">${settings.creativity.toFixed(1)}</span>
        <input type="range" id="ai-creativity" min="0" max="1" step="0.1" value="${settings.creativity}" />
      </label>
    </div>
    
    <button id="ai-settings-close" class="ai-btn ai-btn-primary">Close</button>
  `;
  
  // Position panel near the button
  const btn = document.getElementById('ai-settings-btn');
  const btnRect = btn.getBoundingClientRect();
  panel.style.top = `${btnRect.bottom + 8}px`;
  panel.style.right = '16px';
  
  document.body.appendChild(panel);
  
  // Event listeners
  document.getElementById('ai-enabled').addEventListener('change', (e) => {
    saveSettings({ enabled: e.target.checked });
  });
  
  document.getElementById('ai-choice-style').addEventListener('change', (e) => {
    saveSettings({ aiChoiceStyle: e.target.value });
  });
  
  document.getElementById('ai-loading-indicator').addEventListener('change', (e) => {
    saveSettings({ showLoadingIndicator: e.target.checked });
  });
  
  // Endpoint URL handling
  const endpointInput = document.getElementById('ai-endpoint-url');
  const endpointError = document.getElementById('ai-endpoint-error');
  
  endpointInput.addEventListener('blur', () => {
    const url = endpointInput.value.trim();
    const validation = validateEndpointUrl(url);
    
    if (!validation.valid) {
      endpointError.textContent = validation.reason;
      endpointError.style.display = 'block';
      endpointInput.classList.add('ai-key-input-error');
    } else {
      endpointError.style.display = 'none';
      endpointInput.classList.remove('ai-key-input-error');
      saveSettings({ apiEndpoint: url });
    }
  });
  
  const resetEndpointBtn = document.getElementById('ai-reset-endpoint');
  if (resetEndpointBtn) {
    resetEndpointBtn.addEventListener('click', () => {
      endpointInput.value = DEFAULT_SETTINGS.apiEndpoint;
      saveSettings({ apiEndpoint: DEFAULT_SETTINGS.apiEndpoint });
      showSettingsPanel(); // Refresh panel to update hint
    });
  }
  
  // JSON mode handling
  document.getElementById('ai-json-mode').addEventListener('change', (e) => {
    saveSettings({ useJsonMode: e.target.checked });
  });
  
  const creativitySlider = document.getElementById('ai-creativity');
  const creativityValue = document.getElementById('creativity-value');
  creativitySlider.addEventListener('input', (e) => {
    creativityValue.textContent = parseFloat(e.target.value).toFixed(1);
  });
  creativitySlider.addEventListener('change', (e) => {
    saveSettings({ creativity: parseFloat(e.target.value) });
  });
  
  document.getElementById('ai-update-key').addEventListener('click', async () => {
    panel.remove();
    await showKeyModal({ allowCancel: true, title: 'Update API Key' });
    showSettingsPanel(); // Refresh panel
  });
  
  const clearBtn = document.getElementById('ai-clear-key');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (confirm('Clear your API key? AI features will be disabled until a new key is entered.')) {
        clearApiKey();
        showSettingsPanel(); // Refresh panel
      }
    });
  }
  
  document.getElementById('ai-settings-close').addEventListener('click', () => {
    panel.remove();
  });
  
  // Close on click outside
  setTimeout(() => {
    document.addEventListener('click', function closeHandler(e) {
      if (!panel.contains(e.target) && e.target.id !== 'ai-settings-btn') {
        panel.remove();
        document.removeEventListener('click', closeHandler);
      }
    });
  }, 100);
}

/**
 * Ensures an API key is available, prompting if necessary
 * 
 * @returns {Promise<string|null>} The API key or null if user cancelled
 */
async function ensureApiKey() {
  const key = getApiKey();
  if (key) {
    return key;
  }
  
  return showKeyModal({ 
    allowCancel: true, 
    title: 'API Key Required' 
  });
}

// Inject CSS styles for modal and settings
function injectStyles() {
  if (document.getElementById('ai-key-manager-styles')) {
    return;
  }
  
  const styles = document.createElement('style');
  styles.id = 'ai-key-manager-styles';
  styles.textContent = `
    .ai-modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    
    .ai-modal {
      background: #161b22;
      border: 1px solid #3c4457;
      border-radius: 12px;
      padding: 24px;
      max-width: 400px;
      width: 90%;
    }
    
    .ai-modal-title {
      margin: 0 0 12px 0;
      font-size: 18px;
      color: #e8ecf0;
    }
    
    .ai-modal-desc {
      margin: 0 0 16px 0;
      font-size: 14px;
      color: #9fb3c8;
      line-height: 1.5;
    }
    
    .ai-key-input {
      width: 100%;
      padding: 10px 12px;
      background: #0f1116;
      border: 1px solid #3c4457;
      border-radius: 6px;
      color: #e8ecf0;
      font-size: 14px;
      font-family: monospace;
      box-sizing: border-box;
    }
    
    .ai-key-input:focus {
      outline: none;
      border-color: #58a6ff;
    }
    
    .ai-key-input-error {
      border-color: #f85149 !important;
    }
    
    .ai-key-error {
      color: #f85149;
      font-size: 13px;
      margin-top: 8px;
    }
    
    .ai-modal-buttons {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      margin-top: 16px;
    }
    
    .ai-modal-note {
      margin: 16px 0 0 0;
      font-size: 12px;
      color: #7d8590;
    }
    
    .ai-modal-note a {
      color: #58a6ff;
    }
    
    .ai-btn {
      padding: 8px 16px;
      border-radius: 6px;
      border: 1px solid #3c4457;
      background: #2d3342;
      color: #e8ecf0;
      font-size: 14px;
      cursor: pointer;
      transition: background 120ms ease;
    }
    
    .ai-btn:hover {
      background: #3b4356;
    }
    
    .ai-btn-primary {
      background: #238636;
      border-color: #238636;
    }
    
    .ai-btn-primary:hover {
      background: #2ea043;
    }
    
    .ai-btn-secondary {
      background: transparent;
    }
    
    .ai-btn-small {
      padding: 4px 8px;
      font-size: 12px;
    }
    
    .ai-btn-danger {
      color: #f85149;
    }
    
    .ai-btn-danger:hover {
      background: #f8514922;
    }
    
    .ai-settings-panel {
      position: fixed;
      background: #161b22;
      border: 1px solid #3c4457;
      border-radius: 8px;
      padding: 16px;
      min-width: 280px;
      z-index: 999;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    
    .ai-settings-panel h3 {
      margin: 0 0 16px 0;
      font-size: 16px;
      color: #e8ecf0;
    }
    
    .ai-setting-row {
      margin-bottom: 12px;
      font-size: 14px;
      color: #c9d1d9;
    }
    
    .ai-setting-row label {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    
    .ai-setting-row select {
      background: #0f1116;
      border: 1px solid #3c4457;
      border-radius: 4px;
      color: #e8ecf0;
      padding: 4px 8px;
    }
    
    .ai-setting-row input[type="range"] {
      flex: 1;
      min-width: 100px;
    }
    
    .ai-key-display {
      font-family: monospace;
      color: #7d8590;
    }
    
    #ai-settings-btn {
      background: #2d3342;
      color: #e8ecf0;
      border: 1px solid #3c4457;
      border-radius: 6px;
      padding: 8px 12px;
      cursor: pointer;
    }
    
    #ai-settings-btn:hover {
      background: #3b4356;
    }
    
    .ai-setting-endpoint {
      flex-direction: column;
      align-items: stretch;
    }
    
    .ai-setting-endpoint label {
      flex-direction: column;
      align-items: stretch;
    }
    
    .ai-endpoint-input {
      width: 100%;
      padding: 6px 8px;
      background: #0f1116;
      border: 1px solid #3c4457;
      border-radius: 4px;
      color: #e8ecf0;
      font-size: 12px;
      font-family: monospace;
      margin-top: 4px;
      box-sizing: border-box;
    }
    
    .ai-endpoint-input:focus {
      outline: none;
      border-color: #58a6ff;
    }
    
    .ai-endpoint-hint {
      font-size: 11px;
      color: #7d8590;
      margin-top: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .ai-setting-hint {
      font-size: 11px;
      color: #7d8590;
    }
  `;
  
  document.head.appendChild(styles);
}

// Initialize on load
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      injectStyles();
      initSettingsUI();
    });
  } else {
    injectStyles();
    initSettingsUI();
  }
}

// Export for use in other modules
const ApiKeyManager = {
  getApiKey,
  setApiKey,
  clearApiKey,
  hasApiKey,
  validateKeyFormat,
  validateEndpointUrl,
  maskApiKey,
  getSettings,
  saveSettings,
  getEndpointUrl,
  setEndpointUrl,
  isJsonModeEnabled,
  showKeyModal,
  ensureApiKey,
  initSettingsUI,
  DEFAULT_SETTINGS
};

// CommonJS export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ApiKeyManager;
}

// Browser global export
if (typeof window !== 'undefined') {
  window.ApiKeyManager = ApiKeyManager;
}

})();
