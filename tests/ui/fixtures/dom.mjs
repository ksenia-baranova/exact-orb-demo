// Переиспользуемый листовой DOM-порт для wiring checks. Браузер/layout не имитируются.
export function documentPort() {
  let document;
  function node(tagName = "div", id = "") {
    const listeners = new Map(), attributes = new Map();
    let ownText = "";
    const element = { tagName, id, value: "", checked: false, hidden: false, disabled: false, dataset: {}, children: [], parentNode: null,
      get textContent() { return ownText + this.children.map((child) => child.textContent).join(""); },
      set textContent(value) { ownText = value; this.replaceChildren(); },
      addEventListener(type, listener) { listeners.set(type, listener); },
      emit(type, detail = {}) { return listeners.get(type)?.({ preventDefault() {}, ...detail }); },
      click() { if (!this.disabled) return this.emit("click"); },
      setAttribute(name, value) { attributes.set(name, String(value)); },
      getAttribute(name) {
        if (name.startsWith("data-")) return this.dataset[name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())];
        return attributes.get(name) ?? this[name];
      },
      removeAttribute(name) { attributes.delete(name); },
      insertBefore(child, before) {
        if (child.parentNode) child.parentNode.children = child.parentNode.children.filter((item) => item !== child);
        const index = this.children.indexOf(before);
        this.children.splice(index < 0 ? this.children.length : index, 0, child);
        child.parentNode = this;
      },
      after(child) { const siblings = this.parentNode.children; this.parentNode.insertBefore(child, siblings[siblings.indexOf(this) + 1]); },
      replaceChildren(...items) {
        for (const child of this.children) child.parentNode = null;
        this.children = [];
        this.append(...items);
      },
      append(...items) { for (const item of items) this.insertBefore(item, null); },
      querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; },
      querySelectorAll(selector) {
        const parts = selector.split(" ");
        const descendants = (parent) => parent.children.flatMap((child) => [child, ...descendants(child)]);
        let candidates = [this];
        for (const part of parts) candidates = candidates.flatMap(descendants).filter((candidate) => matches(candidate, part));
        return candidates;
      },
      focus() { document.activeElement = this; },
      setSelectionRange(start, end, direction) { this.selectionStart = start; this.selectionEnd = end; this.selectionDirection = direction; },
    };
    return element;
  }
  function matches(element, selector) {
    if (selector.startsWith("#")) return element.id === selector.slice(1);
    const [, tag, attribute, expected] = selector.match(/^([a-z]+)?(?:\[([^=\]]+)(?:="([^"]*)")?\])?$/) ?? [];
    if (!tag && !attribute) throw new Error(`Unsupported DOM-port selector: ${selector}`);
    return (!tag || element.tagName === tag) && (!attribute || (expected === undefined
      ? element.getAttribute(attribute) !== undefined : element.getAttribute(attribute) === expected));
  }
  const main = node("main"), form = node("form", "birth-form");
  for (const id of ["birth-date", "birth-place", "birth-time", "time-unknown", "terms-acknowledged",
    "place-list", "place-status", "place-retry", "form-error", "date-error", "place-error", "time-error", "acknowledged-error"]) form.append(node("div", id));
  const build = node("button", "build-button"); build.type = "submit"; form.append(build); main.append(form);
  document = { activeElement: null, root: main,
    getElementById: (id) => main.querySelector(`#${id}`), createElement: (tag) => node(tag) };
  return document;
}
