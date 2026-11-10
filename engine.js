// Moteur de logique : calcule quels checks sont accessibles avec l'inventaire donné.
// Hypothèses : entrées non mélangées, le jour et la nuit sont toujours disponibles.
(function (root) {
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, '');
  // names : { nomNormalisé: "Nom affiché" }, sert à afficher les objets requis
  // starts : zones déjà accessibles dès le départ en plus de Célesbourg (ex. « Faron Pillar » si on apparaît à Firone : la tablette n'est alors plus requise)
  function compute(L, inv, over, names, starts) {
    const S = {};
    for (const k in L.settings) S[k] = over && k in over ? over[k] : L.settings[k].d;
    const idx = (n, v) => { const o = L.settings[n].o; return o.length ? o.indexOf(String(v)) : Number(v); };
    const reach = new Set(['Root', ...(starts || [])]), ev = new Set();
    let mc = new Map();
    const have = (i) => inv[i] || 0;
    function E(r) {
      switch (r[0]) {
        case 'N': case 'D': case 'T': return true;
        case 'X': return false;
        case '&': for (let i = 1; i < r.length; i++) if (!E(r[i])) return false; return true;
        case '|': for (let i = 1; i < r.length; i++) if (E(r[i])) return true; return false;
        case '!': return !E(r[1]);
        case 'i': return have(r[1]) > 0;
        case 'c': return have(r[2]) >= r[1];
        case 'e': return ev.has(r[1]);
        case 'a': return reach.has(r[1]);
        case 'w': return [300, 500, 1000, 5000, 9000][Math.min(have('progressivewallet'), 4)] + 300 * have('extrawallet') >= r[1];
        case 'g': return have('gratitudecrystal') + 5 * have('gratitudecrystalpack') >= r[1];
        case 's': {
          const a = idx(r[1], S[r[1]]), b = idx(r[1], r[3]);
          return r[2] === '==' ? a === b : r[2] === '!=' ? a !== b : r[2] === '>=' ? a >= b : a <= b;
        }
        case 'b': return S[r[1]] === 'on' || S[r[1]] === true;
        case 'm': {
          if (!mc.has(r[1])) mc.set(r[1], E(L.macros[r[1]] || ['X']));
          return mc.get(r[1]);
        }
      }
      return false;
    }
    for (let changed = true; changed;) {
      changed = false; mc = new Map();
      for (const a of [...reach]) {
        const A = L.areas[a]; if (!A) continue;
        for (const d in A.x) if (!reach.has(d) && E(A.x[d])) { reach.add(d); changed = true; }
        for (const e in A.e) if (!ev.has(e) && E(A.e[e])) { ev.add(e); changed = true; }
      }
    }
    const locs = new Set(); mc = new Map();
    for (const a of reach) { const A = L.areas[a]; if (A) for (const l in A.l) if (E(A.l[l])) locs.add(l); }

    // ---- Objets manquants pour atteindre un check ----
    // need(règle) = liste des objets/conditions qui manquent (en choisissant l'alternative la plus courte
    // pour les « ou »), ou null si impossible avec les réglages. Calculé à la demande, une seule fois.
    let areaNeed = null, evNeed = null, nmemo = null, locAreas = null; const cache = new Map();
    const nm = (k) => (names && names[k]) || k;
    const U = (a, b) => (a === null || b === null ? null : !b.length ? a : !a.length ? b : [...new Set([...a, ...b])]);
    function N(r) {
      switch (r[0]) {
        case 'N': case 'D': case 'T': return [];
        case 'X': return null;
        case '&': { let acc = []; for (let i = 1; i < r.length && acc; i++) acc = U(acc, N(r[i])); return acc; }
        case '|': { let b = null; for (let i = 1; i < r.length; i++) { const x = N(r[i]); if (!x) continue; if (!x.length) return x; if (!b || x.length < b.length) b = x; } return b; }
        case '!': return E(r[1]) ? null : [];
        case 'i': return have(r[1]) > 0 ? [] : [nm(r[1])];
        case 'c': return have(r[2]) >= r[1] ? [] : [`${nm(r[2])} (${have(r[2])}/${r[1]})`];
        case 'w': return E(r) ? [] : [`Portefeuille ≥ ${r[1]} rubis`];
        case 'g': return E(r) ? [] : [`Gratitude Crystals (${have('gratitudecrystal') + 5 * have('gratitudecrystalpack')}/${r[1]})`];
        case 'e': return evNeed.get(r[1]) || null;
        case 'a': return areaNeed.get(r[1]) || null;
        case 's': case 'b': return E(r) ? [] : null;
        case 'm': {
          if (!nmemo.has(r[1])) nmemo.set(r[1], N(L.macros[r[1]] || ['X']));
          return nmemo.get(r[1]);
        }
      }
      return null;
    }
    const better = (map, k, v) => { if (!v) return false; const o = map.get(k); if (o && o.length <= v.length) return false; map.set(k, v); return true; };
    function prepare() {
      if (areaNeed) return;
      areaNeed = new Map([...reach].map((a) => [a, []])); evNeed = new Map([...ev].map((e) => [e, []]));
      for (let it = 0, ch = true; ch && it < 80; it++) {
        ch = false; nmemo = new Map();
        for (const [a, an] of [...areaNeed]) {
          const A = L.areas[a]; if (!A) continue;
          for (const d in A.x) { const o = areaNeed.get(d); if (o && !o.length) continue; if (better(areaNeed, d, U(an, N(A.x[d])))) ch = true; }
          for (const e in A.e) { const o = evNeed.get(e); if (o && !o.length) continue; if (better(evNeed, e, U(an, N(A.e[e])))) ch = true; }
        }
      }
      nmemo = new Map(); locAreas = {};
      for (const a in L.areas) for (const l in L.areas[a].l) (locAreas[l] = locAreas[l] || []).push(a);
    }
    // -> [] : accessible · [objets…] : ce qu'il manque · null : impossible avec ces réglages
    function needsOf(name) {
      if (locs.has(name)) return [];
      if (cache.has(name)) return cache.get(name);
      prepare(); let b = null;
      for (const a of locAreas[name] || []) {
        const an = areaNeed.get(a); if (!an) continue;
        const x = U(an, N(L.areas[a].l[name]));
        if (x && (!b || x.length < b.length)) b = x;
      }
      cache.set(name, b); return b;
    }
    return { reach, locs, S, ev, needsOf };
  }
  const api = { compute, norm };
  if (typeof module !== 'undefined') module.exports = api; else root.SSHDEngine = api;
})(this);
