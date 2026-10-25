/** Store observable mínimo. El estado es inmutable: `set` fusiona un parche superficial. */

/**
 * @template T
 * @param {T} initial
 */
export function createStore(initial) {
  let state = { ...initial };
  const subscribers = new Set();

  return {
    get: () => state,
    /** @param {Partial<T>} patch */
    set(patch) {
      const prev = state;
      state = { ...state, ...patch };
      const changed = Object.keys(patch).filter((k) => prev[k] !== state[k]);
      if (changed.length) subscribers.forEach((fn) => fn(state, changed, prev));
    },
    /** @returns {() => void} función para cancelar la suscripción */
    subscribe(fn) {
      subscribers.add(fn);
      return () => subscribers.delete(fn);
    },
  };
}

/**
 * Ejecuta `fn(state, changedKeys)` ahora y cada vez que cambie alguna de `keys`.
 * @param {ReturnType<typeof createStore>} store
 * @param {string[]} keys
 * @param {(state:any, changed:string[]) => void} fn
 */
export function watch(store, keys, fn) {
  fn(store.get(), keys);
  return store.subscribe((state, changed) => {
    const hit = changed.filter((k) => keys.includes(k));
    if (hit.length) fn(state, hit);
  });
}
