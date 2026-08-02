/**
 * The eight grammar rules, which are also the event vocabulary.
 * Sections 3-4 of docs/spec/core.md.
 */

import {
  Field,
  MAX_SITES,
  Pair,
  Relation,
  candidates,
  coupling,
  pairKey,
  pairOf,
  scaleMul,
} from "./core.js";

export const BOUNDARY_DECAY = 500;
export const REINFORCE = 1500;
export const JOIN_W = 700;
export const FEEDBACK_W = 600;
export const LEVEL_W = 800;
export const BECOMING_WINDOW = 2;

export type Param = number | number[];

export class Event {
  constructor(
    readonly name: string,
    readonly params: Param[],
  ) {}

  /** Canonical identity, fixed across implementations (spec section 3). */
  key(): string {
    const parts = this.params.map((p) => (Array.isArray(p) ? p.join(",") : String(p)));
    return `${this.name}(${parts.join(";")})`;
  }
}

function asSet(p: Param): Set<number> {
  return new Set(Array.isArray(p) ? p : [p]);
}

/** Canonical minimum-coupling bisection by prefix split. */
export function bisect(f: Field, support: readonly number[]): [number[], number[]] {
  const cpl = coupling(f);
  let bestK = 1;
  let bestCross: number | null = null;
  for (let k = 1; k < support.length; k++) {
    const left = new Set(support.slice(0, k));
    const right = new Set(support.slice(k));
    let cross = 0;
    for (const [key, c] of cpl) {
      const [a, b] = pairOf(key);
      if ((left.has(a) && right.has(b)) || (right.has(a) && left.has(b))) cross += c;
    }
    if (bestCross === null || cross < bestCross) {
      bestK = k;
      bestCross = cross;
    }
  }
  return [support.slice(0, bestK), support.slice(bestK)];
}

function pairClass(r: Relation, s: Set<number>): "inside" | "crossing" | "outside" {
  const na = s.has(r.a);
  const nb = s.has(r.b);
  if (na && nb) return "inside";
  if (na || nb) return "crossing";
  return "outside";
}

function boundaryCoupling(f: Field, s: Set<number>): number {
  let total = 0;
  for (const [k, c] of coupling(f)) {
    const [a, b] = pairOf(k);
    if (s.has(a) !== s.has(b)) total += c;
  }
  return total;
}

/** Non-negative distance to enablement; zero exactly when the event is possible. */
export function gap(f: Field, e: Event): number {
  const p = e.params;
  switch (e.name) {
    case "form_boundary": {
      const s = asSet(p[0]);
      return s.size > 0 && boundaryCoupling(f, s) > 0 ? 0 : 1;
    }
    case "differentiate":
      return Math.max(0, 4 - (p[0] as number[]).length);
    case "join": {
      const s = asSet(p[0]);
      const t = asSet(p[1]);
      const disjoint = [...s].every((x) => !t.has(x));
      return s.size > 0 && t.size > 0 && disjoint ? 0 : 1;
    }
    case "branch":
    case "repeat":
      return Math.max(0, f.sites + (p[0] as number[]).length - MAX_SITES);
    case "feedback":
      return f.relations.some((r) => r.a === p[0] && r.b === p[1]) ? 0 : 1;
    case "new_level":
      return (
        Math.max(0, 2 - (p[0] as number[]).length) + (f.sites < MAX_SITES ? 0 : 1)
      );
    case "dissolve": {
      const s = asSet(p[0]);
      return f.relations.some((r) => pairClass(r, s) === "inside") ? 0 : 1;
    }
    default:
      throw new Error(`unknown event ${e.name}`);
  }
}

export function enabled(f: Field, e: Event): boolean {
  return gap(f, e) === 0;
}

/** Return a new field. The only way a field state may come into being. */
export function apply(f: Field, e: Event, note = ""): Field {
  if (!enabled(f, e)) throw new Error(`precondition not met for ${e.key()}`);
  const g = f.copy();
  const p = e.params;

  switch (e.name) {
    case "form_boundary": {
      const s = asSet(p[0]);
      g.relations = g.relations.map((r) =>
        pairClass(r, s) === "crossing"
          ? { ...r, w: r.w.map((x) => scaleMul(x, BOUNDARY_DECAY)) }
          : r,
      );
      break;
    }
    case "differentiate": {
      const [left, right] = bisect(f, p[0] as number[]);
      const ls = new Set(left);
      const rs = new Set(right);
      g.relations = g.relations.map((r) => {
        const crossing =
          (ls.has(r.a) && rs.has(r.b)) || (rs.has(r.a) && ls.has(r.b));
        const intra =
          (ls.has(r.a) && ls.has(r.b)) || (rs.has(r.a) && rs.has(r.b));
        const factor = crossing ? BOUNDARY_DECAY : intra ? REINFORCE : null;
        return factor === null ? r : { ...r, w: r.w.map((x) => scaleMul(x, factor)) };
      });
      break;
    }
    case "join": {
      const a = Math.min(...(p[0] as number[]));
      const b = Math.min(...(p[1] as number[]));
      g.addRelation(a, b, [JOIN_W, ...Array(g.dims.length - 1).fill(0)]);
      break;
    }
    case "branch":
    case "repeat": {
      const src = p[0] as number[];
      const mapping = new Map<number, number>();
      src.forEach((s, i) => mapping.set(s, g.sites + i));
      g.sites += src.length;
      const inside = new Set(src);
      for (const r of f.relations) {
        const cls = pairClass(r, inside);
        if (cls === "inside") {
          g.addRelation(mapping.get(r.a)!, mapping.get(r.b)!, r.w);
        } else if (cls === "crossing" && e.name === "repeat") {
          if (inside.has(r.a)) g.addRelation(mapping.get(r.a)!, r.b, r.w);
          else g.addRelation(r.a, mapping.get(r.b)!, r.w);
        }
      }
      break;
    }
    case "feedback":
      g.addRelation(p[0] as number, p[1] as number, [
        FEEDBACK_W,
        ...Array(g.dims.length - 1).fill(0),
      ]);
      break;
    case "new_level": {
      const level = g.sites;
      g.sites += 1;
      for (const m of [...(p[0] as number[])].sort((x, y) => x - y)) {
        g.addRelation(m, level, [LEVEL_W, ...Array(g.dims.length - 1).fill(0)]);
      }
      break;
    }
    case "dissolve": {
      const s = asSet(p[0]);
      g.relations = g.relations.filter((r) => pairClass(r, s) !== "inside");
      break;
    }
  }

  g.history.push({ tick: g.tick, name: e.name, params: [...p], note });
  return g;
}

/** The canonical, finite space of event instances considered at a field. */
export function instances(f: Field): Event[] {
  const out: Event[] = [];
  const cands = candidates(f);
  for (const s of cands) {
    for (const name of [
      "form_boundary",
      "differentiate",
      "branch",
      "repeat",
      "new_level",
      "dissolve",
    ]) {
      out.push(new Event(name, [s]));
    }
  }
  for (let i = 0; i < cands.length; i++) {
    for (let j = i + 1; j < cands.length; j++) {
      out.push(new Event("join", [cands[i], cands[j]]));
    }
  }
  const pairs = new Set<Pair>(f.relations.map((r) => pairKey(r.a, r.b)));
  for (const p of [...pairs].sort((x, y) => {
    const [ax, bx] = pairOf(x);
    const [ay, by] = pairOf(y);
    return ax - ay || bx - by;
  })) {
    const [a, b] = pairOf(p);
    out.push(new Event("feedback", [a, b]));
  }
  return out.sort((x, y) => (x.key() < y.key() ? -1 : x.key() > y.key() ? 1 : 0));
}

/** P(x) = transformations accessible from x. */
export function possibility(f: Field): Event[] {
  return instances(f).filter((e) => enabled(f, e));
}

/**
 * Events whose distance to enablement is strictly decreasing.
 * Our reading of 'what is becoming accessible'; tracked as contradictions/003.
 */
export function becomingAccessible(f: Field): Event[] {
  if (f.gapLog.length < BECOMING_WINDOW + 1) return [];
  const window = f.gapLog.slice(-(BECOMING_WINDOW + 1));
  const out: Event[] = [];
  for (const e of instances(f)) {
    const k = e.key();
    const series = window.map((step) => step.get(k));
    if (series.some((v) => v === undefined)) continue;
    const s = series as number[];
    let decreasing = true;
    for (let i = 1; i < s.length; i++) if (!(s[i] < s[i - 1])) decreasing = false;
    if (s[s.length - 1] > 0 && decreasing) out.push(e);
  }
  return out;
}

export function snapshotGaps(f: Field): Map<string, number> {
  const m = new Map<string, number>();
  for (const e of instances(f)) m.set(e.key(), gap(f, e));
  return m;
}
