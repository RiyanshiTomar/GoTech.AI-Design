// Tiny observable store: the whole UI renders from {design, model, status}.
let state = { design: "", model: null, status: null };
const subs = new Set();
export const store = {
  get: () => state,
  set(next) { state = { ...state, ...next }; subs.forEach((fn) => fn(state)); },
  subscribe(fn) { subs.add(fn); fn(state); return () => subs.delete(fn); },
};
