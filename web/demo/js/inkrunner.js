(function() {
  const storyEl = document.getElementById('story');
  const choicesEl = document.getElementById('choices');
  const tagsEl = document.getElementById('tags');
  const saveBtn = document.getElementById('save-btn');
  const loadBtn = document.getElementById('load-btn');
  const durationInput = document.getElementById('smoke-duration');
  const intensityInput = document.getElementById('smoke-intensity');
  const SAVE_KEY = 'ge-hch.smoke.save';

  const DEMO_COMPILED = {"inkVersion":19,"root":[["^Hello from InkJS demo.\n","\n",["ev",["^smoke",["list",{"sp":0,"owner":0},["^smoke"],[[0,0,0],[1,0,0],[2,0,0]]]],"/ev","\n","ev",["str",null],["out","^\n"],"/ev",["ev",["^Do you want to continue?\n","\n",["list",{"sp":0,"owner":0},["^*"],[[0,0,0],[1,0,0],[2,0,0]]],"\n^Or stay here?\n","\n",["list",{"sp":0,"owner":0},["^*"],[[0,0,0],[1,0,0],[2,0,0]]],"\n"],"/ev",["nop"],"/ev","/ev","#","ev",["G",0],"/ev","ev",["list",{"sp":1,"origins":[]},["^smoke"],[[0,0,0],[1,0,0],[2,0,0]]],"/ev","/ev","/ev"],0,[]],"listDefs":{},"defaultEnvironment":"default","names":["default"]};

  let story;

  function logTelemetry(event) {
    console.log(event);
  }

  async function loadStory() {
    if (!window.inkjs || (!inkjs.Story)) {
      console.error('InkJS failed to load');
      return;
    }
    story = new inkjs.Story(DEMO_COMPILED);
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
      story = new inkjs.Story(DEMO_COMPILED);
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


  saveBtn.addEventListener('click', saveState);
  loadBtn.addEventListener('click', loadState);

  window.addEventListener('load', loadStory);
})();
