/**
 * Field, relations, and the derivation of entities.
 * Sections 0-2 of docs/spec/core.md.
 *
 * No function here creates an entity. Entities are computed from relations.
 */

export const SCALE = 1000;
export const THETA = 500;
export const PERSISTENCE = 3;
export const COHESION = 600;
export const MAX_SITES = 64;

/** v * f / SCALE, truncating toward zero (spec section 0). */
export function scaleMul(v: number, f: number): number {
  return Math.trunc((v * f) / SCALE);
}

/** The generator named in spec section 0, masked to 64 bits at each step. */
export function xorshift64s(seed: bigint): bigint {
  const M = (1n << 64n) - 1n;
  let s = seed & M;
  s = (s ^ (s >> 12n)) & M;
  s = (s ^ ((s << 25n) & M)) & M;
  s = (s ^ (s >> 27n)) & M;
  return (s * 0x2545f4914f6cdd1dn) & M;
}

export type Pair = string; // "a,b" with a < b

export function pairKey(a: number, b: number): Pair {
  return a < b ? `${a},${b}` : `${b},${a}`;
}

export function pairOf(p: Pair): [number, number] {
  const [a, b] = p.split(",").map(Number);
  return [a, b];
}

/** Ascending numeric-tuple comparison, matching the reference ordering. */
export function cmpTuple(x: readonly number[], y: readonly number[]): number {
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    if (x[i] !== y[i]) return x[i] - y[i];
  }
  return x.length - y.length;
}

export function cmpPair(x: Pair, y: Pair): number {
  return cmpTuple(pairOf(x), pairOf(y));
}

export interface Relation {
  id: number;
  a: number;
  b: number;
  w: number[];
}

export interface EventRecord {
  tick: number;
  name: string;
  params: unknown[];
  note: string;
}

export class Field {
  dims: string[];
  sites: number;
  relations: Relation[];
  observed: Map<Pair, number>;
  tick: number;
  history: EventRecord[];
  candidateLog: Set<string>[];
  residualStreak: Map<Pair, number>;
  gapLog: Map<string, number>[];
  nextRelationId: number;

  constructor(init: Partial<Field> & { dims: string[]; sites: number; relations: Relation[] }) {
    this.dims = init.dims;
    this.sites = init.sites;
    this.relations = init.relations;
    this.observed = init.observed ?? new Map();
    this.tick = init.tick ?? 0;
    this.history = init.history ?? [];
    this.candidateLog = init.candidateLog ?? [];
    this.residualStreak = init.residualStreak ?? new Map();
    this.gapLog = init.gapLog ?? [];
    this.nextRelationId = init.nextRelationId ?? init.relations.length;
  }

  static seed(
    dims: string[],
    sites: number,
    relations: [number, number, number[]][],
    observed?: Map<Pair, number>,
  ): Field {
    const rels: Relation[] = relations.map(([a, b, w], i) => {
      if (a >= b) throw new Error(`relation endpoints must satisfy a < b, got ${a},${b}`);
      if (w.length !== dims.length) throw new Error("relation weight arity must equal dims");
      return { id: i, a, b, w: [...w] };
    });
    const f = new Field({
      dims: [...dims],
      sites,
      relations: rels,
      observed: new Map(observed ?? []),
      nextRelationId: rels.length,
    });
    f.candidateLog.push(new Set(candidates(f).map((s) => s.join(","))));
    f.gapLog.push(new Map());
    return f;
  }

  copy(): Field {
    return new Field({
      dims: [...this.dims],
      sites: this.sites,
      relations: this.relations.map((r) => ({ ...r, w: [...r.w] })),
      observed: new Map(this.observed),
      tick: this.tick,
      history: [...this.history],
      candidateLog: [...this.candidateLog],
      residualStreak: new Map(this.residualStreak),
      gapLog: [...this.gapLog],
      nextRelationId: this.nextRelationId,
    });
  }

  addRelation(a: number, b: number, w: number[]): void {
    if (a === b) throw new Error("a relation may not join a site to itself");
    const [lo, hi] = a < b ? [a, b] : [b, a];
    this.relations.push({ id: this.nextRelationId++, a: lo, b: hi, w: [...w] });
  }

  digest(): Record<string, unknown> {
    const rels = [...this.relations].sort(
      (x, y) => x.a - y.a || x.b - y.b || x.id - y.id,
    );
    return {
      dims: [...this.dims],
      sites: this.sites,
      tick: this.tick,
      relations: rels.map((r) => [r.a, r.b, [...r.w]]),
      entities: entities(this).map((s) => [...s]),
      residual_total: residualTotal(this),
    };
  }
}

// --- derivation (spec section 2) -------------------------------------------

export function coupling(f: Field): Map<Pair, number> {
  const acc = new Map<Pair, number>();
  for (const r of f.relations) {
    const k = pairKey(r.a, r.b);
    const sum = r.w.reduce((t, x) => t + Math.abs(x), 0);
    acc.set(k, (acc.get(k) ?? 0) + sum);
  }
  return acc;
}

function components(f: Field, cpl: Map<Pair, number>): number[][] {
  const parent = Array.from({ length: f.sites }, (_, i) => i);
  const find = (x: number): number => {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  };
  for (const k of [...cpl.keys()].sort(cmpPair)) {
    if ((cpl.get(k) ?? 0) >= THETA) {
      const [a, b] = pairOf(k);
      const ra = find(a);
      const rb = find(b);
      if (ra !== rb) parent[Math.max(ra, rb)] = Math.min(ra, rb);
    }
  }
  const groups = new Map<number, number[]>();
  for (let s = 0; s < f.sites; s++) {
    const root = find(s);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root)!.push(s);
  }
  return [...groups.values()]
    .filter((g) => g.length >= 2)
    .map((g) => [...g].sort((x, y) => x - y))
    .sort(cmpTuple);
}

export function cohesionHolds(f: Field, support: readonly number[]): boolean {
  const inside = new Set(support);
  let internal = 0;
  let boundary = 0;
  for (const [k, c] of coupling(f)) {
    const [a, b] = pairOf(k);
    const na = inside.has(a);
    const nb = inside.has(b);
    if (na && nb) internal += c;
    else if (na || nb) boundary += c;
  }
  return internal * SCALE >= COHESION * (internal + boundary);
}

/** Components that both hold together and clear the coupling threshold. */
export function candidates(f: Field): number[][] {
  return components(f, coupling(f)).filter((s) => cohesionHolds(f, s));
}

/**
 * Persistent convergences of relations (section 1 of the source text).
 * A candidate becomes an entity only by surviving unchanged for PERSISTENCE ticks.
 */
export function entities(f: Field): number[][] {
  if (f.candidateLog.length < PERSISTENCE) return [];
  const recent = f.candidateLog.slice(-PERSISTENCE);
  const last = recent[recent.length - 1];
  return [...last]
    .filter((s) => recent.every((step) => step.has(s)))
    .map((s) => s.split(",").map(Number))
    .sort(cmpTuple);
}

// --- accountability (spec section 5) ---------------------------------------

export function residual(f: Field, p: Pair): number {
  let modeled = 0;
  for (const r of f.relations) {
    if (pairKey(r.a, r.b) === p) modeled += r.w.reduce((t, x) => t + x, 0);
  }
  return (f.observed.get(p) ?? 0) - modeled;
}

export function allPairs(f: Field): Pair[] {
  const s = new Set<Pair>(f.observed.keys());
  for (const r of f.relations) s.add(pairKey(r.a, r.b));
  return [...s].sort(cmpPair);
}

export function residualTotal(f: Field): number {
  return allPairs(f).reduce((t, p) => t + Math.abs(residual(f, p)), 0);
}
