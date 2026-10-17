// Optional callback support. Static pages do not include this script.
(() => {
  if (window.fluorine) return;
  let api = null;
  const pending = new Set();
  const invoke = (target, name, args) => {
    if (!Object.prototype.hasOwnProperty.call(target, name) || typeof target[name] !== 'function') {
      return Promise.reject(new Error('Fluorine callback is not registered: ' + name));
    }
    return Promise.resolve().then(() => target[name](...args));
  };
  window.fluorine = {
    connect(target) {
      api = target;
      for (const entry of pending) {
        clearTimeout(entry.timer);
        invoke(api, entry.name, entry.args).then(entry.resolve, entry.reject);
      }
      pending.clear();
    },
    call(name, ...args) {
      if (api) return invoke(api, name, args);
      return new Promise((resolve, reject) => {
        const entry = {name, args, resolve, reject};
        entry.timer = setTimeout(() => {
          pending.delete(entry);
          reject(new Error('Python callbacks require a connected host such as Sulfur.'));
        }, 10000);
        pending.add(entry);
      });
    }
  };
  // Compatibility with hosts that expose a pywebview API directly.
  const connect = () => {
    if (window.pywebview && window.pywebview.api) window.fluorine.connect(window.pywebview.api);
  };
  window.addEventListener('pywebviewready', connect);
  connect();
})();
