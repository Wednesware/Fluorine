const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../fluorine/bridge.js'), 'utf8');

function context() {
  const listeners = {};
  const timers = new Map();
  let timerId = 0;
  const window = {addEventListener: (name, handler) => { listeners[name] = handler; }};
  vm.runInNewContext(source, {
    window, Promise, Error, Set,
    setTimeout: callback => { timers.set(++timerId, callback); return timerId; },
    clearTimeout: id => timers.delete(id)
  });
  return {window, listeners, timers};
}

(async () => {
  const {window, timers} = context();
  const pending = window.fluorine.call('move', 'right');
  let calls = 0;
  window.fluorine.connect({move: direction => { calls++; return direction; }});
  assert.equal(await pending, 'right');
  assert.equal(calls, 1);
  assert.equal(timers.size, 0);
  assert.equal(await window.fluorine.call('move', 'left'), 'left');
  await assert.rejects(window.fluorine.call('missing'), /not registered/);
  await assert.rejects(window.fluorine.call('toString'), /not registered/);
  window.fluorine.connect({fail: () => { throw new Error('callback failed'); }});
  await assert.rejects(window.fluorine.call('fail'), /callback failed/);

  const standalone = context();
  const rejected = assert.rejects(standalone.window.fluorine.call('move'), /require a connected host/);
  for (const timer of standalone.timers.values()) timer();
  await rejected;

  const legacy = context();
  legacy.window.pywebview = {api: {move: () => 7}};
  legacy.listeners.pywebviewready();
  assert.equal(await legacy.window.fluorine.call('move'), 7);
  console.log('Callback bridge checks passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
