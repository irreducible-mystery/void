/**
 * Ontologies, lossy translation, worlds, and observers.
 * Sections 8-10 of docs/spec/core.md.
 */

import { Field, SCALE, coupling, entities, pairKey, pairOf, scaleMul } from "./core.js";
import { instances } from "./events.js";

export const ONTOLOGIES: Record<string, [string, string, string]> = {
  O1: ["objects", "properties", "causes"],
  O2: ["processes", "relations", "constraints"],
  O3: ["agents", "meanings", "purposes"],
};

export interface Observer {
  site: number;
  back_action: number;
}

/** Observers must declare back-action explicitly, even when it is zero. */
export function observer(site: number, back_action: number | null | undefined): Observer {
  if (back_action === null || back_action === undefined) {
    throw new Error("back_action must be declared explicitly, even when zero");
  }
  return { site, back_action };
}

export function readOntology(f: Field, name: string, observers: Observer[] = []): string[] {
  const terms: string[] = [];
  const obs = [...observers].sort((a, b) => a.site - b.site);
  const pairs = [...new Set(f.relations.map((r) => pairKey(r.a, r.b)))].sort((x, y) => {
    const [ax, bx] = pairOf(x);
    const [ay, by] = pairOf(y);
    return ax - ay || bx - by;
  });

  if (name === "O1") {
    for (const s of entities(f)) terms.push(`object:${s.join("-")}`);
    for (const d of f.dims) terms.push(`property:${d}`);
    for (const p of pairs) terms.push(`cause:${pairOf(p).join("-")}`);
  } else if (name === "O2") {
    for (const n of [...new Set(f.history.map((h) => h.name))].sort())
      terms.push(`process:${n}`);
    for (const p of pairs) terms.push(`relation:${pairOf(p).join("-")}`);
    for (const n of [...new Set(instances(f).map((e) => e.name))].sort())
      terms.push(`constraint:${n}`);
  } else if (name === "O3") {
    for (const o of obs) terms.push(`agent:${o.site}`);
    for (const o of obs) terms.push(`meaning:${o.site}`);
    for (const e of instances(f).slice(0, 1)) terms.push(`purpose:${e.key()}`);
  } else {
    throw new Error(`unknown ontology ${name}`);
  }
  return terms;
}

/** Absence is the point: an empty target becomes residue rather than being dropped. */
const CORRESPONDENCE: Record<string, Record<string, string | null>> = {
  "O1->O2": { object: "process", cause: "relation", property: null },
  "O2->O1": { process: "object", relation: "cause", constraint: null },
  "O1->O3": { object: "agent", property: "meaning", cause: null },
  "O3->O1": { agent: "object", meaning: "property", purpose: null },
  "O2->O3": { process: "purpose", relation: "meaning", constraint: null },
  "O3->O2": { meaning: "relation", purpose: "process", agent: null },
};

export class Translation {
  constructor(
    readonly source: string,
    readonly target: string,
    readonly image: string[],
    readonly residue: string[],
  ) {}

  loss(): number {
    const total = this.image.length + this.residue.length;
    if (total === 0) return 0;
    return Math.floor((this.residue.length * SCALE) / total);
  }
}

/**
 * F : O_i -> O_j, returning both the translation and its residue.
 * There is deliberately no variant that returns the image alone.
 */
export function translate(terms: string[], source: string, target: string): Translation {
  const table = CORRESPONDENCE[`${source}->${target}`];
  if (!table) throw new Error(`no correspondence ${source}->${target}`);
  const image: string[] = [];
  const residue: string[] = [];
  for (const t of terms) {
    const idx = t.indexOf(":");
    const kind = idx < 0 ? t : t.slice(0, idx);
    const rest = idx < 0 ? "" : t.slice(idx + 1);
    const mapped = table[kind];
    if (mapped) image.push(`${mapped}:${rest}`);
    else residue.push(t);
  }
  return new Translation(source, target, image, residue);
}

// --- worlds ----------------------------------------------------------------

export class World {
  constructor(
    readonly name: string,
    readonly relevance: Record<string, number>,
  ) {}

  support(f: Field): number[] {
    const live = new Set<number>();
    f.dims.forEach((d, i) => {
      if ((this.relevance[d] ?? 0) !== 0) live.add(i);
    });
    const sites = new Set<number>();
    for (const r of f.relations) {
      if (r.w.some((v, i) => live.has(i) && v !== 0)) {
        sites.add(r.a);
        sites.add(r.b);
      }
    }
    return [...sites].sort((x, y) => x - y);
  }
}

/** Defined only where both worlds have purchase; elsewhere absent, never defaulted. */
export function partialMap(f: Field, wi: World, wj: World): Map<number, number> {
  const si = new Set(wi.support(f));
  const sj = new Set(wj.support(f));
  const m = new Map<number, number>();
  for (const s of [...si].filter((x) => sj.has(x)).sort((x, y) => x - y)) m.set(s, s);
  return m;
}

export function sharedWorld(f: Field, wi: World, wj: World, name: string): World {
  const rel: Record<string, number> = {};
  for (const d of f.dims) {
    const v = Math.min(wi.relevance[d] ?? 0, wj.relevance[d] ?? 0);
    if (v !== 0) rel[d] = v;
  }
  return new World(name, rel);
}

// --- observers -------------------------------------------------------------

/** Measure, and in measuring, change what was measured. */
export function read(f: Field, o: Observer): [number, Field] {
  let reading = 0;
  for (const [k, c] of coupling(f)) {
    const [a, b] = pairOf(k);
    if (a === o.site || b === o.site) reading += c;
  }
  if (o.back_action === 0) return [reading, f];

  const g = f.copy();
  g.relations = g.relations.map((r) =>
    r.a === o.site || r.b === o.site
      ? { ...r, w: r.w.map((x) => scaleMul(x, o.back_action)) }
      : r,
  );
  g.history.push({
    tick: g.tick,
    name: "observation",
    params: [o.site],
    note: `back_action=${o.back_action}`,
  });
  return [reading, g];
}
