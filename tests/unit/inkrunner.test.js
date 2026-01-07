const path = require('path');

describe('inkrunner core', () => {
  let inkrunner;
  let story;
  let storyEl;
  let choicesEl;
  let tagsEl;
  let durationInput;
  let intensityInput;
  let saveBtn;
  let loadBtn;

  const buildDOM = () => {
    document.body.innerHTML = `
      <div id="story"></div>
      <div id="choices"></div>
      <div id="tags"></div>
      <button id="save-btn"></button>
      <button id="load-btn"></button>
      <input id="smoke-duration" value="3" />
      <input id="smoke-intensity" value="5" />
    `;
    storyEl = document.getElementById('story');
    choicesEl = document.getElementById('choices');
    tagsEl = document.getElementById('tags');
    durationInput = document.getElementById('smoke-duration');
    intensityInput = document.getElementById('smoke-intensity');
    saveBtn = document.getElementById('save-btn');
    loadBtn = document.getElementById('load-btn');
  };

  const mockStory = ({ canContinue = false, currentChoices = [], currentTags = [], continueImpl } = {}) => {
    const state = {
      toJson: jest.fn(() => 'story-state'),
      LoadJson: jest.fn(),
    };
    const storyObj = {
      canContinue,
      currentChoices,
      currentTags,
      state,
      Continue: jest.fn(() => {
        if (continueImpl) return continueImpl(storyObj);
        return 'continued text';
      }),
      ChooseChoiceIndex: jest.fn(),
    };
    return storyObj;
  };

  beforeEach(() => {
    jest.resetModules();
    buildDOM();
    story = mockStory();

    global.window.inkjs = { Story: function Stub() {}, Compiler: function Stub() {} };
    global.window.Smoke = {
      trigger: jest.fn(),
      getState: jest.fn(() => ({ smoke: 'state' })),
      loadState: jest.fn(),
    };

    jest.spyOn(global.window, 'addEventListener').mockImplementation(() => {});

    jest.isolateModules(() => {
      inkrunner = require(path.join(process.cwd(), 'web/demo/js/inkrunner.js'));
      inkrunner.setStory(story);
    });
  });

  it('appendText creates a div with text', () => {
    inkrunner.appendText('hello');
    expect(storyEl.textContent).toBe('hello');
    expect(storyEl.querySelectorAll('div')).toHaveLength(1);
  });

  it('renderChoices creates buttons and handles clicks', () => {
    const choiceStory = mockStory({ currentChoices: [{ text: 'A' }, { text: 'B' }] });
    inkrunner.setStory(choiceStory);

    inkrunner.renderChoices();

    const buttons = choicesEl.querySelectorAll('button.choice-btn');
    expect(buttons).toHaveLength(2);
    expect(buttons[0].textContent).toBe('A');

    buttons[1].dispatchEvent(new window.Event('click'));
    expect(choiceStory.ChooseChoiceIndex).toHaveBeenCalledWith(1);
    expect(storyEl.innerHTML).toBe('');
  });

  it('renderChoices handles touchstart', () => {
    const choiceStory = mockStory({ currentChoices: [{ text: 'A' }, { text: 'B' }] });
    inkrunner.setStory(choiceStory);

    inkrunner.renderChoices();
    const buttons = choicesEl.querySelectorAll('button.choice-btn');

    buttons[0].dispatchEvent(new window.Event('touchstart'));

    expect(choiceStory.ChooseChoiceIndex).toHaveBeenCalledWith(0);
  });

  it('handleTags renders tags and triggers smoke', () => {
    durationInput.value = '7';
    intensityInput.value = '9';

    inkrunner.handleTags(['smoke', 'cool']);

    expect(tagsEl.textContent).toBe('Tags: smoke, cool');
    expect(window.Smoke.trigger).toHaveBeenCalledWith({ duration: 7, intensity: 9 });
  });

  it('handleTags shows none when empty', () => {
    inkrunner.handleTags([]);
    expect(tagsEl.textContent).toBe('Tags: none');
  });

  it('saveState writes to localStorage', () => {
    const setItem = jest.spyOn(window.localStorage.__proto__, 'setItem');
    inkrunner.setStory(story);

    inkrunner.saveState();

    expect(setItem).toHaveBeenCalledTimes(1);
    const [key, value] = setItem.mock.calls[0];
    expect(key).toBe('ge-hch.smoke.save');
    expect(JSON.parse(value)).toEqual({
      story: 'story-state',
      smoke: { smoke: 'state' },
      config: { duration: 3, intensity: 5 },
    });
    expect(key).toBe('ge-hch.smoke.save');
    expect(JSON.parse(value)).toEqual({
      story: 'story-state',
      smoke: { smoke: 'state' },
      config: { duration: 3, intensity: 5 },
    });
  });

  it('loadState restores story, smoke, inputs, and continues', () => {
    const saved = {
      story: 'saved-story',
      smoke: { s: 1 },
      config: { duration: 11, intensity: 13 },
    };
    window.localStorage.setItem('ge-hch.smoke.save', JSON.stringify(saved));

    const continuingStory = mockStory({
      canContinue: true,
      continueImpl: (s) => {
        s.canContinue = false;
        return 'restored text';
      },
    });
    inkrunner.setStory(continuingStory);

    inkrunner.loadState();

    expect(continuingStory.state.LoadJson).toHaveBeenCalledWith('saved-story');
    expect(window.Smoke.loadState).toHaveBeenCalledWith({ s: 1 });
    expect(durationInput.value).toBe('11');
    expect(intensityInput.value).toBe('13');
    expect(tagsEl.textContent).toBe('Tags: none');
    expect(storyEl.textContent).toContain('restored text');
  });
});
