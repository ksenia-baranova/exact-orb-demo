// REQ-WHEEL-01/10/11: live host belongs solely to this controller.
// Internal same-origin module discipline; not a JS security sandbox.
const NS = "http://www.w3.org/2000/svg";
const TAGS = new Set(["svg", "g", "circle", "path", "line", "rect", "text", "title", "desc"]);
const NUMERIC = new Set(["x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "stroke-width"]);
const NONNEGATIVE = new Set(["r", "rx", "ry", "width", "height", "stroke-width"]);
const DATA = new Set(["data-sector", "data-house", "data-aspect", "data-source-index", "data-anchor",
  "data-symbol", "data-house-number", "data-house-sector", "data-degree-tick", "data-label", "data-kind", "data-point-house", "data-row", "data-selected", "data-component", "data-leader", "data-leader-bridge"]);
export class SvgPresentationError extends Error {
  constructor(code) { super(code); this.name = "SvgPresentationError"; this.code = code; }
}
class ControllerFailure extends Error {
  constructor(cause) { super("controller failure", { cause }); }
}
const fail = code => { throw new SvgPresentationError(code); };
const finite = value => value.trim() !== "" && Number.isFinite(Number(value)) && Math.abs(Number(value)) <= 1e7;
function numbers(value, length) {
  const parts = value.trim().split(/[\s,]+/);
  return (!length || parts.length === length) && parts.every(finite);
}
export function validatePassiveSvg(root) {
  if (root?.namespaceURI !== NS || root.localName !== "svg") fail("root");
  let count = 0;
  for (const n of [root, ...root.querySelectorAll("*")]) {
    if (++count > 10000 || n.namespaceURI !== NS || !TAGS.has(n.localName)) fail("element");
    for (const a of n.attributes) {
      const key = a.name, value = a.value;
      if (value.length > 8192) fail("attribute-length");
      if (NUMERIC.has(key)) {
        if (!finite(value) || NONNEGATIVE.has(key) && Number(value) < 0) fail("numeric");
      } else if (DATA.has(key) || key === "aria-label") {
        if (/[\u0000-\u001f]/.test(value)) fail("text");
      } else if (key === "xmlns") { if (value !== NS) fail("namespace"); }
      else if (key === "role") { if (value !== "img") fail("role"); }
      else if (key === "focusable") { if (value !== "false") fail("focus"); }
      else if (key === "overflow") { if (value !== "hidden") fail("overflow"); }
      else if (key === "viewBox") { if (!numbers(value, 4) || value.trim().split(/[\s,]+/).slice(2).some(v => Number(v) <= 0)) fail("viewbox"); }
      else if (key === "font-size") { if (![12, 16].includes(Number(value))) fail("font-size"); }
      else if (key === "font-family") { if (value !== '"Segoe UI Symbol", "Segoe UI", sans-serif') fail("font-family"); }
      else if (key === "fill" || key === "stroke") { if (!/^(?:#[0-9a-fA-F]{6}|white|none)$/.test(value)) fail("paint"); }
      else if (key === "opacity") { if (!finite(value) || Number(value) < 0 || Number(value) > 1) fail("opacity"); }
      else if (key === "stroke-dasharray") { if (value !== "none" && (!numbers(value) || value.trim().split(/[\s,]+/).some(v => Number(v) < 0))) fail("dash"); }
      else if (key === "transform") { if (!/^translate\([^()]+\)$/.test(value) || !numbers(value.slice(10, -1), 2)) fail("transform"); }
      else if (key === "d") {
        const residue = value.replace(/[MLAZ]/g, " ").replace(/[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi, token => finite(token) ? " " : "?");
        if (!/^[\s,]*$/.test(residue) || !/^[MLAZ\d\s,.\-+e]+$/i.test(value)) fail("path");
      } else fail("attribute:" + key);
    }
    if (n.childNodes && [...n.childNodes].some(child => ![1, 3].includes(child.nodeType))) fail("node-type");
  }
}
function immutableCopy(value) {
  const copy = structuredClone(value);
  const freeze = item => { if (item && typeof item === "object") { Object.values(item).forEach(freeze); Object.freeze(item); } };
  freeze(copy); return copy;
}
export function createDrawingController({ document, imageHost, measureHost, factory,
  onUnavailable, onFatal, onEvent = () => {} }) {
  let current = null, revision = 0, closed = false, leaf = null, activeFactory = factory;
  const disposed = new WeakSet();
  const emit = (event, lease, detail = null) => onEvent({ event, revision: lease?.revision, acceptanceSeq: lease?.acceptanceSeq, detail });
  const trusted = action => { try { return action(); } catch (error) { throw new ControllerFailure(error); } };
  function revoke(lease) {
    if (!lease) return;
    lease.valid = false;
    if (lease.surface.parentNode) lease.surface.parentNode.removeChild(lease.surface);
    emit("revoke", lease);
  }
  function disposeOnce(instance, lease) {
    if (!instance || disposed.has(instance)) return;
    disposed.add(instance);
    try { instance.dispose(); emit("dispose", lease); }
    catch (error) { emit("dispose-fault", lease, String(error)); }
  }
  function localFailure(lease, error) {
    if (!lease.valid || current !== lease || closed) { emit("stale-rejection", lease); return false; }
    revoke(lease);
    if (current !== lease || closed) return false;
    trusted(() => imageHost.replaceChildren());
    emit("svg-unavailable", lease, error.code ?? error.name ?? "leaf");
    trusted(() => onUnavailable?.({ kind: "svg_unavailable", code: error.code ?? "renderer" }));
    return false;
  }
  function publish(lease, root) {
    if (closed || !lease.valid || current !== lease) { emit("stale-refused", lease); return false; }
    try {
      validatePassiveSvg(root);
      const copy = root.cloneNode(true);
      if (closed || !lease.valid || current !== lease) return false;
      validatePassiveSvg(copy);
      if (closed || !lease.valid || current !== lease) return false;
      trusted(() => imageHost.replaceChildren(copy));
      trusted(() => onUnavailable?.(null));
      emit("install-copy", lease); return true;
    } catch (error) {
      if (error instanceof ControllerFailure) throw error;
      return localFailure(lease, error);
    }
  }
  function present(prepare, { replace = false, rendererFactory = activeFactory } = {}) {
    if (closed) return Promise.resolve(false);
    const prior = current, retired = replace || rendererFactory !== activeFactory ? leaf : null;
    const ownRevision = ++revision;
    revoke(prior);
    if (revision !== ownRevision || closed) return Promise.resolve(false);
    imageHost.replaceChildren();
    const surface = document.createElement("div");
    const lease = { valid: true, surface, revision: ownRevision, acceptanceSeq: null };
    current = lease; emit("remove", lease);
    if (!lease.valid || current !== lease || closed) return Promise.resolve(false);
    // State/index/HTML and snapshot creation are OUTSIDE the leaf guard.
    if (retired) leaf = null;
    let snapshot;
    try {
      const prepared = prepare(); emit("html", lease);
      snapshot = prepared === null ? null : immutableCopy(prepared);
      lease.acceptanceSeq = snapshot?.acceptanceSeq;
    } catch (error) { disposeOnce(retired, lease); throw error; }
    disposeOnce(retired, lease);
    if (!lease.valid || current !== lease) return Promise.resolve(false);
    activeFactory = rendererFactory;
    if (snapshot === null) { revoke(lease); current = null; disposeOnce(leaf, lease); leaf = null; return Promise.resolve(true); }
    measureHost.append(surface);
    let output;
    try {
      if (!leaf) {
        const candidate = activeFactory(surface);
        if (!candidate || typeof candidate.update !== "function" || typeof candidate.dispose !== "function") throw new SvgPresentationError("renderer-interface");
        if (!lease.valid || current !== lease || closed) {
          if (candidate !== leaf) disposeOnce(candidate, lease);
          return Promise.resolve(false);
        }
        leaf = candidate;
      }
      emit("draw", lease);
      output = leaf.update(snapshot, root => publish(lease, root), surface);
    } catch (error) {
      if (error instanceof ControllerFailure) throw error.cause;
      return Promise.resolve(localFailure(lease, error));
    }
    return Promise.resolve(output).then(() => lease.valid && current === lease, error => {
      if (error instanceof ControllerFailure) {
        if (closed || !lease.valid || current !== lease) { emit("stale-controller-rejection", lease); return false; }
        revoke(lease);
        if (closed || current !== lease) return false;
        imageHost.replaceChildren();
        if (onFatal) { onFatal(error.cause); return false; }
        throw error.cause;
      }
      return localFailure(lease, error);
    });
  }
  return Object.freeze({
    present,
    close() {
      if (closed) return;
      closed = true;
      const last = current;
      revoke(last); current = null; imageHost.replaceChildren();
      disposeOnce(leaf, last); leaf = null;
    },
  });
}
