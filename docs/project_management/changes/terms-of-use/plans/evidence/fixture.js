// TASK-D-04 only: observable leaf requests and trusted click recipients.
const q = new URLSearchParams(location.search);
const calls = [], clicks = [];
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  const call = { path: args[0], method: args[1]?.method || 'GET', pending: true };
  calls.push(call);
  try { return await originalFetch(...args); }
  finally { call.pending = false; render(); }
};
function render() {
  const output = document.getElementById('browser-evidence');
  if (output) output.textContent = JSON.stringify({ calls, clicks, userAgent: navigator.userAgent });
}
document.addEventListener('click', event => {
  clicks.push({ target: event.target.id || event.target.tagName, trusted: event.isTrusted,
    x: event.clientX, y: event.clientY });
  render();
}, true);
document.addEventListener('DOMContentLoaded', () => {
  const output = document.createElement('pre');
  output.id = 'browser-evidence'; output.hidden = true; document.body.append(output);
  const target = document.getElementById(q.get('target'));
  if (target) {
    const style = document.createElement('style');
    if (q.get('control') === 'small') style.textContent = `#${target.id}{width:43px!important;height:43px!important;min-width:0!important;min-height:0!important;padding:0!important;overflow:hidden!important;}`;
    if (q.get('control') === 'clip') style.textContent = `#${target.id}{clip-path:inset(0 calc(50% - 16px) 0 0)!important;}`;
    document.head.append(style);
    if (q.get('control') === 'overlay') {
      const overlay = document.createElement('div'); overlay.id = 'negative-overlay';
      const update = () => { const r=target.getBoundingClientRect(); overlay.style.cssText = `position:fixed;left:${r.x+r.width/2-4}px;top:${r.y+r.height/2-4}px;width:8px;height:8px;z-index:9999;background:red;`; };
      document.body.append(overlay); addEventListener('scroll', update, true); update();
    }
  }
  render();
});
