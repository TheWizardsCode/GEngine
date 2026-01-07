describe('telemetry facade', () => {
  let Telemetry;

  beforeEach(() => {
    jest.resetModules();
    jest.isolateModules(() => {
      Telemetry = require('../../web/demo/js/telemetry.js');
    });
    Telemetry.enable();
  });

  it('emits via console.log when enabled', () => {
    const spy = jest.spyOn(console, 'log').mockImplementation(() => {});

    Telemetry.emit('story_start');
    Telemetry.emit('choice_selected', { idx: 0 });

    expect(spy).toHaveBeenCalledWith('story_start');
    expect(spy).toHaveBeenCalledWith('choice_selected', { idx: 0 });

    spy.mockRestore();
  });

  it('does not emit when disabled', () => {
    const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
    Telemetry.disable();

    Telemetry.emit('story_start');
    Telemetry.emit('choice_selected');

    expect(spy).not.toHaveBeenCalled();

    spy.mockRestore();
  });
});
