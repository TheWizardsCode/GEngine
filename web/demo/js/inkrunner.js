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
  const STORY_JSON_PATH = './story.json';
  // Embedded fallback if fetch fails (compiled via inkjs CLI)
  const DEMO_COMPILED = {"inkVersion":21,"root":[[{"->":"start"},["done",{"#n":"g-0"}],null],"done",{"start":[["^Hello from InkJS demo.","\n","#","^smoke","/#","ev",true,"/ev",{"VAR=":"seen_smoke","re":true},["ev",{"^->":"start.0.9.$r1"},{"temp=":"$r"},"str",{"->":".^.s"},[{"#n":"$r1"}],"/str","/ev",{"*":'.^. ^.c-0','flg':18},{"s":["^Do you want to continue? ",{"->":"$r","var":true},null]}],["ev",{"^->":"start.0.10.$r1"},{"temp=":"$r"},"str",{"->":".^.s"},[{"#n":"$r1"}],"/str","/ev",{"*":'.^. ^.c-1','flg':18},{"s":["^Or stay here? ",{"->":"$r","var":true},null]}],{"c-0":["ev",{"^->":"start.0.c-0.$r2"},"/ev",{"temp=":"$r"},{"->":".^.^.9.s"},[{"#n":"$r2"}],{"->":"choice_one"},"\n",{"#f":5}],"c-1":["ev",{"^->":"start.0.c-1.$r2"},"/ev",{"temp=":"$r"},{"->":".^.^.10.s"},[{"#n":"$r2"}],{"->":"choice_two"},"\n",{"#f":5}]}],null],"choice_one":[["^You move forward.","\n",["^DONE","\n",{"#n":"g-0"}],null],null],"choice_two":[["^You decide to stay. The smoke clears.","\n",["^DONE","\n",{"#n":"g-0"}],null],null],"global decl":["ev",false,{"VAR=":"seen_smoke"},"/ev","end",null]}],"listDefs":{}};

  let story;

  function logTelemetry(event) {
    console.log(event);
  }

  async function loadStory() {
    if (!window.inkjs || (!inkjs.Story)) {
      console.error('InkJS failed to load');
      return;
    }
    let compiled = DEMO_COMPILED;
    // If served over HTTP, try loading precompiled JSON from ./story.json (in web/demo/).
    if (window.location.protocol.startsWith('http')) {
      try {
        const res = await fetch(STORY_JSON_PATH, { cache: 'no-cache' });
        if (res.ok) {
          compiled = await res.json();
        }
      } catch (err) {
        console.warn('Using embedded compiled story (fetch failed or not served over HTTP).');
      }
    }
    try {
      story = new inkjs.Story(compiled);
    } catch (err) {
      console.error('Failed to load Ink story', err);
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
      let compiled = DEMO_COMPILED;
      story = new inkjs.Story(compiled);
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
