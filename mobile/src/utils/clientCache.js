/**
 * Client-side cache + SWR (stale-while-revalidate) hook.
 *
 * Pattern: show cached data INSTANTLY, fetch fresh in the background, update
 * the UI when the fresh data lands. This is what makes apps feel "instant".
 *
 * Two layers:
 *   • L1 — JS Map in process memory  (microseconds)
 *   • L2 — AsyncStorage              (~1-3 ms, survives app restarts)
 *
 * Inflight dedupe: if multiple components mount and request the same key
 * within the same tick, only one network request goes out.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useRef, useState } from 'react';

const memCache = new Map();    // key → { value, t }
const inflight = new Map();    // key → Promise
const subscribers = new Map(); // key → Set<(value)=>void>

const PREFIX = 'swr:';

const _now = () => Date.now();

async function _readDisk(key) {
  try {
    const raw = await AsyncStorage.getItem(PREFIX + key);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

async function _writeDisk(key, entry) {
  try { await AsyncStorage.setItem(PREFIX + key, JSON.stringify(entry)); } catch {}
}

function _notify(key, value) {
  const subs = subscribers.get(key);
  if (subs) subs.forEach((fn) => { try { fn(value); } catch {} });
}

/**
 * Get the currently-cached value (memory, falling back to disk).
 * Returns the inner `value` or null on miss.
 */
export async function getCached(key) {
  const m = memCache.get(key);
  if (m) return m.value;
  const d = await _readDisk(key);
  if (d) {
    memCache.set(key, d);
    return d.value;
  }
  return null;
}

export async function setCached(key, value) {
  const entry = { value, t: _now() };
  memCache.set(key, entry);
  _notify(key, value);
  await _writeDisk(key, entry);
}

export async function invalidateCached(...keys) {
  for (const key of keys) {
    memCache.delete(key);
    try { await AsyncStorage.removeItem(PREFIX + key); } catch {}
    _notify(key, null);
  }
}

/**
 * Stale-while-revalidate hook.
 *
 *   const { data, loading, error, refresh } = useCachedFetch(
 *     `profile:${userId}`,
 *     () => usersAPI.getProfile(userId).then(r => r.data),
 *     { staleAfterMs: 30_000 }
 *   );
 *
 * Behavior on mount:
 *   1. Reads cached value from memory → disk. If found, hydrates `data`
 *      INSTANTLY and `loading=false`.
 *   2. If cache age > staleAfterMs (or missing), kicks off a background fetch.
 *   3. When fresh data arrives, updates state + memory + disk.
 *
 * `key` may be null/falsy — the hook will pause until you give it a key.
 */
export function useCachedFetch(key, fetcher, options = {}) {
  const { staleAfterMs = 30_000, enabled = true } = options;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(async () => {
    if (!enabled || !key || !fetcherRef.current) return null;

    // Dedupe — only one in-flight fetch per key
    if (inflight.has(key)) return inflight.get(key);

    const p = (async () => {
      try {
        const result = await fetcherRef.current();
        if (result !== undefined) {
          await setCached(key, result);
          setData(result);
          setError(null);
        }
        return result;
      } catch (e) {
        setError(e);
        return null;
      } finally {
        setLoading(false);
        inflight.delete(key);
      }
    })();

    inflight.set(key, p);
    return p;
  }, [key, enabled]);

  useEffect(() => {
    if (!enabled || !key) {
      setLoading(false);
      return;
    }

    let alive = true;

    // Subscribe so other components writing the same key update us live
    const subs = subscribers.get(key) || new Set();
    const sub = (val) => { if (alive && val !== null) setData(val); };
    subs.add(sub);
    subscribers.set(key, subs);

    (async () => {
      const cached = await getCached(key);
      if (alive && cached !== null) {
        setData(cached);
        setLoading(false);
      }
      // Decide whether to revalidate
      const m = memCache.get(key);
      const fresh = m && _now() - m.t < staleAfterMs;
      if (!fresh) {
        await refresh();
      } else {
        // Cache fresh enough — still mark loading false for safety
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
      const set = subscribers.get(key);
      if (set) {
        set.delete(sub);
        if (set.size === 0) subscribers.delete(key);
      }
    };
  }, [key, enabled, staleAfterMs, refresh]);

  return { data, loading, error, refresh };
}

/**
 * Fire-and-forget prefetch. Useful at app start to warm common keys.
 *   prefetch(`feed:home`, () => contentAPI.list().then(r=>r.data))
 */
export function prefetch(key, fetcher) {
  if (!key || !fetcher || inflight.has(key)) return;
  const m = memCache.get(key);
  if (m && _now() - m.t < 5_000) return;   // very fresh, skip
  const p = (async () => {
    try {
      const v = await fetcher();
      if (v !== undefined) await setCached(key, v);
    } catch {} finally { inflight.delete(key); }
  })();
  inflight.set(key, p);
}
