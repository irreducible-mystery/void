/**
 * Runner for the shared conformance corpus.
 * Mirrors impl/python/gfield/conformance.py exactly.
 */

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { Field, Pair, entities } from "./core.js";
import { Event, becomingAccessible, possibility } from "./events.js";
import { step } from "./dynamics.js";
import {
  ONTOLOGIES,
  World,
  observer,
  partialMap,
  read,
  readOntology,
  translate,
} from "./views.js";

export interface Vector {
  id: string;
  level: number;
  description: string;
  seed: { dims: string[]; sites: number; relations: [number, number, number[]][]; observed?: Record<string, number> };
  schedule?: ({ name: string | null; params: unknown[]; observe?: Record<string, number> } | null)[];
  check_translation?: boolean;
  check_observer?: { site: number; back_action: number };
  check_worlds?: { a: { name: string; relevance: Record<string, number> }; b: { name: string; relevance: Record<string, number> } };
  expect: { digest?: Record<string, unknown>; checks?: Record<string, unknown>; hand_written?: Record<string, unknown> };
}

/** Search upward for the corpus, so this works from src/ and from dist/ alike. */
export function corpusDir(): string {
  let dir = dirname(fileURLToPath(import.meta.url));
  for (let i = 0; i < 8; i++) {
    const candidate = join(dir, "conformance", "vectors");
    if (existsSync(candidate)) return candidate;
    const parent = resolve(dir, "..");
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error("conformance/vectors not found above " + fileURLToPath(import.meta.url));
}

export function loadCorpus(dir = corpusDir()): Vector[] {
  return readdirSync(dir)
    .filter((n) => n.endsWith(".json"))
    .sort()
    .map((n) => JSON.parse(readFileSync(join(dir, n), "utf8")) as Vector);
}

function toObserved(o?: Record<string, number>): Map<Pair, number> {
  return new Map(Object.entries(o ?? {}));
}

export function build(seed: Vector["seed"]): Field {
  return Field.seed(seed.dims, seed.sites, seed.relations, toObserved(seed.observed));
}

export function runVector(vec: Vector): { digest: Record<string, unknown>; checks: Record<string, unknown> } {
  let f = build(vec.seed);
  for (const entry of vec.schedule ?? []) {
    let e: Event | null = null;
    let obs: Map<Pair, number> | null = null;
    if (entry !== null) {
      if (entry.name) {
        e = new Event(
          entry.name,
          entry.params.map((p) => (Array.isArray(p) ? (p as number[]) : (p as number))),
        );
      }
      if (entry.observe) obs = toObserved(entry.observe);
    }
    f = step(f, e, obs);
  }

  const digest = f.digest();
  const checks: Record<string, unknown> = {
    dimension_count: f.dims.length,
    residual_total: digest.residual_total,
    entity_count: entities(f).length,
    accessible_count: possibility(f).length,
    becoming_count: becomingAccessible(f).length,
    generated_dimension: f.history.some((h) => h.name === "dimension"),
    history_complete: f.history.every((h) => h.tick <= f.tick),
  };

  if (vec.check_translation) {
    const obs = [observer(0, 0)];
    const losses: Record<string, number> = {};
    for (const src of Object.keys(ONTOLOGIES)) {
      for (const tgt of Object.keys(ONTOLOGIES)) {
        if (src === tgt) continue;
        losses[`${src}->${tgt}`] = translate(readOntology(f, src, obs), src, tgt).loss();
      }
    }
    checks.translation_losses = losses;
    checks.all_losses_positive = Object.values(losses).every((v) => v > 0);
  }

  if (vec.check_observer) {
    const before = entities(f).map((s) => [...s]);
    const probe = observer(vec.check_observer.site, vec.check_observer.back_action);
    let [, g] = read(f, probe);
    for (let i = 0; i < 3; i++) g = step(g, null);
    const after = entities(g).map((s) => [...s]);
    checks.entities_before_observation = before;
    checks.entities_after_observation = after;
    checks.observation_changed_field = JSON.stringify(before) !== JSON.stringify(after);
  }

  if (vec.check_worlds) {
    const wi = new World(vec.check_worlds.a.name, vec.check_worlds.a.relevance);
    const wj = new World(vec.check_worlds.b.name, vec.check_worlds.b.relevance);
    const m = partialMap(f, wi, wj);
    const union = new Set([...wi.support(f), ...wj.support(f)]);
    checks.world_a_support = wi.support(f);
    checks.world_b_support = wj.support(f);
    checks.partial_map_domain = [...m.keys()].sort((x, y) => x - y);
    checks.map_is_partial = m.size < union.size;
  }

  return { digest, checks };
}

/** Order-insensitive structural equality, so key order never causes a false failure. */
function canonical(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(canonical).join(",")}]`;
  if (v && typeof v === "object") {
    const o = v as Record<string, unknown>;
    return `{${Object.keys(o)
      .sort()
      .map((k) => `${JSON.stringify(k)}:${canonical(o[k])}`)
      .join(",")}}`;
  }
  return JSON.stringify(v);
}

export function compare(expected: Vector["expect"], actual: ReturnType<typeof runVector>): string[] {
  const failures: string[] = [];
  if (expected.digest) {
    const e = expected.digest;
    const a = actual.digest;
    for (const k of [...new Set([...Object.keys(e), ...Object.keys(a)])].sort()) {
      if (canonical(e[k]) !== canonical(a[k])) {
        failures.push(`digest.${k}: expected ${canonical(e[k])}, got ${canonical(a[k])}`);
      }
    }
  }
  for (const [k, want] of Object.entries(expected.checks ?? {})) {
    const got = actual.checks[k];
    if (canonical(want) !== canonical(got)) {
      failures.push(`checks.${k}: expected ${canonical(want)}, got ${canonical(got)}`);
    }
  }
  return failures;
}

export function checkAll(dir = corpusDir()): { passed: number; failures: string[] } {
  let passed = 0;
  const failures: string[] = [];
  for (const vec of loadCorpus(dir)) {
    const problems = compare(vec.expect, runVector(vec));
    if (problems.length > 0) failures.push(...problems.map((p) => `[${vec.id}] ${p}`));
    else passed++;
  }
  return { passed, failures };
}
