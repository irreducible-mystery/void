/**
 * Dimension generation, the coupled step, and individuation.
 * Sections 5-7 of docs/spec/core.md. The load-bearing module.
 */

import {
  Field,
  PERSISTENCE,
  Pair,
  allPairs,
  candidates,
  entities,
  pairKey,
  pairOf,
  residual,
  residualTotal,
} from "./core.js";
import { Event, apply, bisect, possibility, snapshotGaps } from "./events.js";

export const TAU = 100;
export const WINDOW = 3;

export function contradictions(f: Field): Pair[] {
  return allPairs(f).filter((p) => Math.abs(residual(f, p)) > TAU);
}

/**
 * Can any presently accessible transformation reduce the total residual?
 * The source text requires irreducibility, not merely persistence.
 */
export function reducibleWithinSpace(f: Field): boolean {
  const base = residualTotal(f);
  for (const e of possibility(f)) {
    try {
      if (residualTotal(apply(f, e)) < base) return true;
    } catch {
      continue;
    }
  }
  return false;
}

/** F_n -> F_{n+1}: add the coordinate the old space could not express. */
export function generateDimension(f: Field): Field {
  const g = f.copy();
  const name = `d${g.dims.length}`;
  g.dims.push(name);

  const firstOfPair = new Map<Pair, number>();
  for (const r of [...g.relations].sort((x, y) => x.a - y.a || x.b - y.b || x.id - y.id)) {
    const k = pairKey(r.a, r.b);
    if (!firstOfPair.has(k)) firstOfPair.set(k, r.id);
  }

  g.relations = g.relations.map((r) => {
    const k = pairKey(r.a, r.b);
    const extra = firstOfPair.get(k) === r.id ? residual(f, k) : 0;
    return { ...r, w: [...r.w, extra] };
  });

  // A pair the old space could not express at all gets its first relation here.
  const covered = new Set<Pair>(g.relations.map((r) => pairKey(r.a, r.b)));
  const uncovered = [...g.observed.keys()]
    .filter((p) => !covered.has(p))
    .sort((x, y) => {
      const [ax, bx] = pairOf(x);
      const [ay, by] = pairOf(y);
      return ax - ay || bx - by;
    });
  for (const p of uncovered) {
    const res = residual(f, p);
    if (res !== 0) {
      const [a, b] = pairOf(p);
      g.addRelation(a, b, [...Array(g.dims.length - 1).fill(0), res]);
    }
  }

  g.residualStreak = new Map();
  g.history.push({
    tick: g.tick,
    name: "dimension",
    params: [name],
    note: "persistent contradiction -> new distinction -> expanded space",
  });
  g.history.push({
    tick: g.tick,
    name: "migration",
    params: [name],
    note: `all prior records extended with coordinate ${name}; prior fields take 0 there`,
  });
  return g;
}

/** One tick of both dynamics (spec section 6). */
export function step(
  f: Field,
  event: Event | null = null,
  observe: Map<Pair, number> | null = null,
): Field {
  let g = event !== null ? apply(f, event) : f.copy();
  g.tick += 1;

  if (observe && observe.size > 0) {
    for (const [k, v] of observe) g.observed.set(k, v);
    g.history.push({
      tick: g.tick,
      name: "accountability",
      params: [...observe.keys()].sort(),
      note: "what the field answers to changed",
    });
  }

  for (const p of allPairs(g)) {
    if (Math.abs(residual(g, p)) > TAU) {
      g.residualStreak.set(p, (g.residualStreak.get(p) ?? 0) + 1);
    } else {
      g.residualStreak.set(p, 0);
    }
  }

  const persistent = [...g.residualStreak.values()].some((v) => v >= WINDOW);
  if (persistent && !reducibleWithinSpace(g)) g = generateDimension(g);

  g.candidateLog.push(new Set(candidates(g).map((s) => s.join(","))));
  g.gapLog.push(snapshotGaps(g));
  return g;
}

export type ScheduleItem =
  | Event
  | null
  | { event: Event | null; observe: Map<Pair, number> | null };

function normalize(item: ScheduleItem): [Event | null, Map<Pair, number> | null] {
  if (item !== null && typeof item === "object" && "event" in item) {
    return [item.event, item.observe];
  }
  return [item as Event | null, null];
}

export function run(f: Field, schedule: ScheduleItem[]): Field {
  let g = f;
  for (const item of schedule) {
    const [e, obs] = normalize(item);
    g = step(g, e, obs);
  }
  return g;
}

// --- individuation (spec section 7) ---------------------------------------

export interface Individual {
  support: number[];
  born_at: number;
  formation_event: string;
  maintained_by: number[];
  dissolution_condition: string;
  suppressed: number[][];
  died_at: number | null;
}

export class Registry {
  open = new Map<string, Individual>();
  closed: Individual[] = [];
  private pending: number[][] = [];
  private pendingTtl = 0;

  observe(f: Field, formationEvent = "seed", suppressed: number[][] = []): void {
    if (suppressed.length > 0) {
      this.pending = suppressed.map((s) => [...s]);
      this.pendingTtl = PERSISTENCE + 1;
    }
    const present = new Set(entities(f).map((s) => s.join(",")));
    const born = [...present].filter((k) => !this.open.has(k)).sort();

    for (const k of born) {
      const support = k.split(",").map(Number);
      const inside = new Set(support);
      this.open.set(k, {
        support,
        born_at: f.tick,
        formation_event: formationEvent,
        maintained_by: f.relations
          .filter((r) => inside.has(r.a) && inside.has(r.b))
          .map((r) => r.id)
          .sort((x, y) => x - y),
        dissolution_condition: "coupling below THETA",
        suppressed: this.pendingTtl > 0 ? this.pending.map((s) => [...s]) : [],
        died_at: null,
      });
    }
    if (born.length > 0 && this.pendingTtl > 0) {
      this.pending = [];
      this.pendingTtl = 0;
    } else if (this.pendingTtl > 0) {
      this.pendingTtl -= 1;
    }

    for (const k of [...this.open.keys()].filter((k) => !present.has(k)).sort()) {
      const ind = this.open.get(k)!;
      this.open.delete(k);
      ind.died_at = f.tick;
      this.closed.push(ind);
    }
  }

  all(): Individual[] {
    return [...this.closed, ...this.open.values()].sort(
      (x, y) =>
        x.born_at - y.born_at ||
        (x.support.join(",") < y.support.join(",") ? -1 : 1),
    );
  }
}

/** Every viable bisection of a support, so the unchosen ones can be recorded. */
export function alternatives(f: Field, support: readonly number[]): number[][] {
  const [chosen] = bisect(f, support);
  const key = chosen.join(",");
  const out: number[][] = [];
  for (let k = 1; k < support.length; k++) {
    const prefix = support.slice(0, k);
    if (prefix.join(",") !== key) out.push(prefix);
  }
  return out;
}

export function runTracked(f: Field, schedule: ScheduleItem[]): [Field, Registry] {
  const reg = new Registry();
  let g = f;
  reg.observe(g);
  for (const item of schedule) {
    const [e, obs] = normalize(item);
    const suppressed =
      e !== null && e.name === "differentiate"
        ? alternatives(g, e.params[0] as number[])
        : [];
    g = step(g, e, obs);
    reg.observe(g, e ? e.name : "drift", suppressed);
  }
  return [g, reg];
}
