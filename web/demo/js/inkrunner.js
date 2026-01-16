(function() {
"use strict";
  const storyEl = document.getElementById('story');
  const choicesEl = document.getElementById('choices');
  const tagsEl = document.getElementById('tags');
  const saveBtn = document.getElementById('save-btn');
  const loadBtn = document.getElementById('load-btn');
  const durationInput = document.getElementById('smoke-duration');
  const intensityInput = document.getElementById('smoke-intensity');
  const SAVE_KEY = 'ge-hch.smoke.save';
  // Support GitHub Pages project path prefixes (e.g., /GEngine/demo/)
  const STORY_PATH = `${window.location.pathname.split('/demo')[0] || ''}/stories/demo.ink`;

  let story;
  
  // ============================================================================
  // AI Writer Integration
  // ============================================================================
  
  /**
   * Current AI proposal being displayed (if any)
   * @type {Object|null}
   */
  let currentAIProposal = null;
  
  /**
   * Loading indicator element
   * @type {HTMLElement|null}
   */
  let loadingIndicator = null;
  
  /**
   * Creates and returns the loading indicator element
   * @returns {HTMLElement}
   */
  function createLoadingIndicator() {
    if (loadingIndicator) {
      return loadingIndicator;
    }
    
    loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'ai-loading-indicator';
    loadingIndicator.className = 'ai-loading';
    loadingIndicator.innerHTML = `
      <span class="ai-loading-spinner"></span>
      <span class="ai-loading-text">Generating AI choice...</span>
    `;
    loadingIndicator.style.display = 'none';
    
    // Inject loading indicator styles if not present
    if (!document.getElementById('ai-writer-styles')) {
      const styles = document.createElement('style');
      styles.id = 'ai-writer-styles';
      styles.textContent = `
        .ai-loading {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: #1c2128;
          border: 1px dashed #3c4457;
          border-radius: 6px;
          color: #7d8590;
          font-size: 13px;
        }
        
        .ai-loading-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid #3c4457;
          border-top-color: #58a6ff;
          border-radius: 50%;
          animation: ai-spin 0.8s linear infinite;
        }
        
        @keyframes ai-spin {
          to { transform: rotate(360deg); }
        }
        
        .choice-btn.ai-choice {
          background: linear-gradient(135deg, #1c2128 0%, #2d333b 100%);
          border-color: #58a6ff;
          border-style: dashed;
          position: relative;
        }
        
        .choice-btn.ai-choice::before {
          content: 'AI';
          position: absolute;
          top: -8px;
          right: 8px;
          background: #58a6ff;
          color: #0d1117;
          font-size: 10px;
          font-weight: bold;
          padding: 2px 6px;
          border-radius: 4px;
        }
        
        .choice-btn.ai-choice:hover {
          background: linear-gradient(135deg, #2d333b 0%, #3b4356 100%);
          border-color: #79c0ff;
        }
        
        .choice-btn.ai-choice-normal {
          /* Normal style - blends in with other choices */
          background: #2d3342;
          border-color: #3c4457;
          border-style: solid;
        }
        
        .choice-btn.ai-choice-normal::before {
          display: none;
        }
        
        .ai-content {
          padding: 16px;
          background: #161b22;
          border-left: 3px solid #58a6ff;
          margin: 12px 0;
          font-style: italic;
        }
        
        .ai-content-label {
          font-size: 11px;
          color: #58a6ff;
          margin-bottom: 8px;
          font-style: normal;
          font-weight: bold;
        }
      `;
      document.head.appendChild(styles);
    }
    
    return loadingIndicator;
  }
  
  /**
   * Shows the loading indicator in the choices area
   */
  function showLoadingIndicator() {
    const settings = window.ApiKeyManager?.getSettings() || {};
    if (!settings.showLoadingIndicator) {
      return;
    }
    
    const indicator = createLoadingIndicator();
    indicator.style.display = 'flex';
    choicesEl.appendChild(indicator);
  }
  
  /**
   * Hides the loading indicator
   */
  function hideLoadingIndicator() {
    if (loadingIndicator) {
      loadingIndicator.style.display = 'none';
      if (loadingIndicator.parentNode) {
        loadingIndicator.parentNode.removeChild(loadingIndicator);
      }
    }
  }
  
  /**
   * Generates an AI branch proposal for the current story state
   * @returns {Promise<Object|null>} The proposal or null on failure
   */
  async function generateAIProposal() {
    // Check if AI is enabled and has API key
    const settings = window.ApiKeyManager?.getSettings() || {};
    if (!settings.enabled) {
      return null;
    }
    
    const apiKey = window.ApiKeyManager?.getApiKey();
    if (!apiKey) {
      return null;
    }
    
    // Check all required modules are loaded
    if (!window.LoreAssembler || !window.PromptEngine || !window.LLMAdapter || !window.ProposalValidator) {
      console.warn('[inkrunner] AI Writer modules not fully loaded');
      return null;
    }
    
    try {
      // Step 1: Assemble LORE context
      const lore = window.LoreAssembler.assembleLORE(story);
      
      // Step 2: Get valid return paths
      const validReturnPaths = window.LoreAssembler.getValidReturnPaths(lore.game_state.current_scene);
      
      // Step 3: Build prompt
      const { systemPrompt, userPrompt, templateType } = window.PromptEngine.buildAutoPrompt(lore, validReturnPaths);
      
      console.debug('[inkrunner] Generating AI proposal', { 
        scene: lore.game_state.current_scene,
        templateType,
        validReturnPaths
      });
      
      // Step 4: Call LLM
      const proposal = await window.LLMAdapter.generateProposal({
        systemPrompt,
        userPrompt,
        apiKey,
        creativity: settings.creativity || 0.7,
        timeoutMs: 5000,
        baseUrl: settings.apiEndpoint || window.LLMAdapter.DEFAULT_BASE_URL,
        useJsonMode: settings.useJsonMode !== false
      });
      
      // Check for errors
      if (proposal.error) {
        console.warn('[inkrunner] AI generation failed:', proposal.message);
        return null;
      }
      
      // Step 5: Validate proposal
      const validation = window.ProposalValidator.quickValidate(proposal);
      if (!validation.valid) {
        console.warn('[inkrunner] AI proposal failed validation:', validation.reason);
        return null;
      }
      
      // Add metadata
      proposal.id = window.LLMAdapter.generateProposalId();
      proposal.validReturnPaths = validReturnPaths;
      
      console.debug('[inkrunner] AI proposal generated:', proposal);
      return proposal;
      
    } catch (e) {
      console.error('[inkrunner] AI generation error:', e);
      return null;
    }
  }
  
  /**
   * Plays the AI-generated branch content
   * @param {Object} proposal - The AI proposal to play
   */
  function playAIBranch(proposal) {
    if (!proposal || !proposal.content) {
      console.error('[inkrunner] Invalid AI proposal');
      return;
    }
    
    // Clear current story display
    storyEl.innerHTML = '';
    
    // Display AI-generated content with styling
    const contentDiv = document.createElement('div');
    contentDiv.className = 'ai-content';
    contentDiv.innerHTML = `
      <div class="ai-content-label">AI-Generated Branch</div>
      <div class="ai-content-text">${escapeHtml(proposal.content.text)}</div>
    `;
    storyEl.appendChild(contentDiv);
    
    // Record this as a choice in LORE history
    if (window.LoreAssembler) {
      window.LoreAssembler.recordChoice(`[AI] ${proposal.choice_text}`);
    }
    
    // Log telemetry
    logTelemetry('ai_branch_played', {
      proposal_id: proposal.id,
      return_path: proposal.content.return_path
    });
    
    // Navigate to return path
    const returnPath = proposal.content.return_path;
    try {
      // Try to navigate to the return path knot
      story.ChoosePathString(returnPath);
      console.debug('[inkrunner] Navigating to return path:', returnPath);
    } catch (e) {
      console.warn(`[inkrunner] Return path "${returnPath}" not found, continuing from current position`, e);
      // Fall back - just continue from current position
    }
    
    // Clear the current AI proposal
    currentAIProposal = null;
    
    // Continue the story
    continueStory();
  }
  
  /**
   * Escapes HTML special characters for safe display
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
  }


  function logTelemetry(event, payload) {
    if (window.Telemetry && typeof window.Telemetry.emit === 'function') {
      window.Telemetry.emit(event, payload);
    } else {
      console.log(event, payload);
    }
  }

  async function loadStory() {
    if (!window.inkjs || (!inkjs.Story)) {
      console.error('InkJS failed to load');
      return;
    }
    if (!inkjs.Compiler) {
      console.error('InkJS Compiler missing; ensure vendor/ink.js is the ink-full build and server serves /demo/vendor/ink.js fresh.');
      return;
    }
    let source;
    try {
      const res = await fetch(STORY_PATH, { cache: 'no-cache' });
      if (!res.ok) {
        console.error(`Failed to fetch Ink story at ${STORY_PATH} (status ${res.status}). Serve from repo root or web/.`);
        return;
      }
      source = await res.text();
    } catch (err) {
      console.error(`Failed to fetch Ink story at ${STORY_PATH}`, err);
      return;
    }
    try {
      const compiled = new inkjs.Compiler(source).Compile();
      story = compiled instanceof inkjs.Story ? compiled : new inkjs.Story(compiled);
    } catch (err) {
      console.error('Failed to load Ink story', err, { usingSource: 'fetched', protocol: window.location.protocol });
      return;
    }
    
    // Clear LORE history on new story load
    if (window.LoreAssembler) {
      window.LoreAssembler.clearHistory();
    }
    
    logTelemetry('story_start');
    storyEl.innerHTML = '';
    choicesEl.innerHTML = '';
    continueStory();
  }



  function continueStory() {
    if (!story) return;
    while (story.canContinue) {
      const text = story.Continue().trim();
      appendText(text);
      handleTags(story.currentTags || []);
    }
    renderChoices();
    if (!story.canContinue && story.currentChoices.length === 0) {
      logTelemetry('story_complete');
    }
  }

  function appendText(text) {
    const div = document.createElement('div');
    div.textContent = text;
    storyEl.appendChild(div);
  }

  /**
   * Renders choices including AI-generated option
   */
  async function renderChoices() {
    choicesEl.innerHTML = '';
    const choices = story.currentChoices || [];
    
    // Render standard choices first
    choices.forEach((choice, idx) => {
      const btn = document.createElement('button');
      btn.className = 'choice-btn';
      btn.textContent = choice.text;
      btn.addEventListener('click', () => {
        handleChoiceSelection(idx, choice.text);
      });
      btn.addEventListener('touchstart', () => {
        handleChoiceSelection(idx, choice.text);
      }, { passive: true });
      choicesEl.appendChild(btn);
    });
    
    // Only try to add AI choice if there are existing choices
    // (don't add AI option to story endings)
    if (choices.length > 0) {
      await addAIChoice();
    }
  }
  
  /**
   * Handles selection of a standard (non-AI) choice
   * @param {number} idx - Choice index
   * @param {string} choiceText - Text of the choice for LORE tracking
   */
  function handleChoiceSelection(idx, choiceText) {
    // Record choice in LORE history
    if (window.LoreAssembler) {
      window.LoreAssembler.recordChoice(choiceText);
    }
    
    logTelemetry('choice_selected');
    story.ChooseChoiceIndex(idx);
    storyEl.innerHTML = '';
    currentAIProposal = null; // Clear any pending AI proposal
    continueStory();
  }
  
  /**
   * Attempts to generate and add an AI choice to the choices list
   */
  async function addAIChoice() {
    const settings = window.ApiKeyManager?.getSettings() || {};
    
    // Check if AI is enabled
    if (!settings.enabled) {
      return;
    }
    
    // Check if we have an API key
    if (!window.ApiKeyManager?.hasApiKey()) {
      return;
    }
    
    // Show loading indicator
    showLoadingIndicator();
    
    try {
      // Generate AI proposal
      const proposal = await generateAIProposal();
      
      // Hide loading indicator
      hideLoadingIndicator();
      
      if (!proposal) {
        // Silently skip if generation failed
        return;
      }
      
      // Store current proposal
      currentAIProposal = proposal;
      
      // Create AI choice button
      const btn = document.createElement('button');
      const styleClass = settings.aiChoiceStyle === 'normal' ? 'ai-choice-normal' : 'ai-choice';
      btn.className = `choice-btn ${styleClass}`;
      btn.textContent = proposal.choice_text;
      
      btn.addEventListener('click', () => {
        playAIBranch(proposal);
      });
      btn.addEventListener('touchstart', () => {
        playAIBranch(proposal);
      }, { passive: true });
      
      choicesEl.appendChild(btn);
      
      logTelemetry('ai_choice_generated', {
        proposal_id: proposal.id,
        scene: proposal._meta?.scene
      });
      
    } catch (e) {
      console.error('[inkrunner] Failed to add AI choice:', e);
      hideLoadingIndicator();
    }
  }

  function handleTags(tags) {
    if (!tags || tags.length === 0) {
      tagsEl.textContent = 'Tags: none';
      return;
    }
    tagsEl.textContent = `Tags: ${tags.join(', ')}`;
    if (tags.includes('smoke')) {
      logTelemetry('smoke_triggered');
      window.Smoke.trigger({
        duration: Number(durationInput.value) || 3,
        intensity: Number(intensityInput.value) || 5,
      });
    }
  }

  function saveState() {
    if (!story) return;
    const payload = {
      story: story.state.toJson(),
      smoke: window.Smoke.getState(),
      config: {
        duration: Number(durationInput.value) || 3,
        intensity: Number(intensityInput.value) || 5,
      },
      // Save LORE choice history
      loreHistory: window.LoreAssembler?.getChoiceHistory() || []
    };
    localStorage.setItem(SAVE_KEY, JSON.stringify(payload));
  }
 
  function loadState() {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return;
    if (!window.inkjs || (!inkjs.Story)) {
      console.error('InkJS failed to load');
      return;
    }
    try {
      const payload = JSON.parse(raw);
      story.state.LoadJson(payload.story);
      durationInput.value = payload.config?.duration ?? durationInput.value;
      intensityInput.value = payload.config?.intensity ?? intensityInput.value;
      window.Smoke.loadState(payload.smoke);
      
      // Restore LORE choice history if available
      if (window.LoreAssembler && payload.loreHistory) {
        window.LoreAssembler.clearHistory();
        payload.loreHistory.forEach(choice => {
          window.LoreAssembler.recordChoice(choice.text);
        });
      }
      
      storyEl.innerHTML = '';
      handleTags(story.currentTags || []);
      continueStory();
    } catch (err) {
      console.error('Failed to load save', err);
    }
  }

  function setStory(testStory) {
    story = testStory;
  }

  const testingExports = {
    appendText,
    renderChoices,
    handleTags,
    saveState,
    loadState,
    continueStory,
    setStory,
    // AI Writer exports for testing
    generateAIProposal,
    playAIBranch,
    handleChoiceSelection
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = testingExports;
  }

  if (typeof window !== 'undefined') {
    window.__inkrunner = testingExports;
  }

  saveBtn.addEventListener('click', saveState);
  loadBtn.addEventListener('click', loadState);

  window.addEventListener('load', loadStory);
})();
