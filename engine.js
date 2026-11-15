// Moteur de logique : calcule quels checks sont accessibles avec l'inventaire donné.
// Hypothèses : entrées non mélangées, le jour et la nuit sont toujours disponibles.
(function (root) {
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, '');
  function compute(L, inv, over, er, forced) { // er = { ov: {connexion: zone d'arrivée}, closed: Set de connexions inconnues }
    const S = {};
    for (const k in L.settings) S[k] = over && k in over ? over[k] : L.settings[k].d;
    const idx = (n, v) => { const o = L.settings[n].o; return o.length ? o.indexOf(String(v)) : Number(v); };
    const reach = new Set(['Root', ...(forced || [])]), ev = new Set(); // forced = zones déjà atteintes par le joueur
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
        for (const d in A.x) {
          let dest = d;
          if (er) { const k = a + ' -> ' + d; if (er.ov[k]) dest = er.ov[k]; else if (er.closed.has(k)) continue; }
          if (!reach.has(dest) && E(A.x[d])) { reach.add(dest); changed = true; }
        }
        for (const e in A.e) if (!ev.has(e) && E(A.e[e])) { ev.add(e); changed = true; }
      }
    }
    const locs = new Set(); mc = new Map();
    for (const a of reach) { const A = L.areas[a]; if (A) for (const l in A.l) if (E(A.l[l])) locs.add(l); }
    return { reach, locs, S };
  }
  const api = { compute, norm };
  if (typeof module !== 'undefined') module.exports = api; else root.SSHDEngine = api;
})(this);
