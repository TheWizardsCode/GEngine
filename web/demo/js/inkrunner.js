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
  const STORY_PATH = '/stories/demo.ink';

  let story;


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

  function renderChoices() {
    choicesEl.innerHTML = '';
    const choices = story.currentChoices || [];
    choices.forEach((choice, idx) => {
      const btn = document.createElement('button');
      btn.className = 'choice-btn';
      btn.textContent = choice.text;
      btn.addEventListener('click', () => {
        logTelemetry('choice_selected');
        story.ChooseChoiceIndex(idx);
        storyEl.innerHTML = '';
        continueStory();
      });
      btn.addEventListener('touchstart', () => {
        logTelemetry('choice_selected');
        story.ChooseChoiceIndex(idx);
        storyEl.innerHTML = '';
        continueStory();
      }, { passive: true });
      choicesEl.appendChild(btn);
    });
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
      }
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
