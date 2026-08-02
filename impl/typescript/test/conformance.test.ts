/**
 * The TypeScript implementation against the shared corpus, plus the principles
 * that are checkable from outside the reference implementation.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { Field, entities, residualTotal, scaleMul, xorshift64s } from "../src/core.js";
import { Event, possibility } from "../src/events.js";
import { runTracked, step } from "../src/dynamics.js";
import { World, observer, partialMap, read, readOntology, translate } from "../src/views.js";
import { checkAll, loadCorpus, runVector } from "../src/conformance.js";

const triangle = () =>
  Field.seed(
    ["d0"],
    6,
    [
      [0, 1, [600]],
      [1, 2, [600]],
      [0, 2, [600]],
    ],
    new Map([
      ["0,1", 900],
      ["1,2", 600],
      ["0,2", 600],
    ]),
  );

const balanced = () =>
  Field.seed(
    ["d0"],
    6,
    [
      [0, 1, [600]],
      [1, 2, [600]],
      [0, 2, [600]],
    ],
    new Map([
      ["0,1", 600],
      ["1,2", 600],
      ["0,2", 600],
    ]),
  );

test("the shared corpus passes", () => {
  const { passed, failures } = checkAll();
  assert.deepEqual(failures, [], failures.join("\n"));
  assert.equal(passed, loadCorpus().length);
});

test("hand-written spec expectations hold", () => {
  for (const vec of loadCorpus()) {
    const actual = runVector(vec);
    assert.ok(vec.expect.hand_written, `${vec.id} has no hand-written expectation`);
    for (const [k, want] of Object.entries(vec.expect.hand_written!)) {
      assert.deepEqual(actual.checks[k], want, `${vec.id}: ${k}`);
    }
  }
});

test("principle 1 -- entities are a function of relations alone", () => {
  let f = balanced();
  for (let i = 0; i < 3; i++) f = step(f, null);
  assert.deepEqual(entities(f), [[0, 1, 2]]);

  let g = Field.seed(["d0"], 6, []);
  for (let i = 0; i < 3; i++) g = step(g, null);
  assert.deepEqual(entities(g), []);
});

test("principle 5 -- the space itself can grow", () => {
  let f = triangle();
  assert.equal(f.dims.length, 1);
  assert.equal(residualTotal(f), 300);
  for (let i = 0; i < 3; i++) f = step(f, null);
  assert.equal(f.dims.length, 2, "the field failed to generate a dimension");
  assert.equal(residualTotal(f), 0, "the coordinate must absorb what produced it");
});

test("principle 5 -- a field in accord invents nothing", () => {
  let f = balanced();
  for (let i = 0; i < 5; i++) f = step(f, null);
  assert.equal(f.dims.length, 1);
});

test("principle 6 -- back-action must be declared", () => {
  assert.throws(() => observer(0, null));
  assert.throws(() => observer(0, undefined));
});

test("principle 6 -- observation changes what is observed", () => {
  let f = balanced();
  for (let i = 0; i < 3; i++) f = step(f, null);
  const before = entities(f);
  let [reading, g] = read(f, observer(0, 100));
  assert.ok(reading > 0);
  for (let i = 0; i < 3; i++) g = step(g, null);
  assert.notDeepEqual(entities(g), before);
});

test("ontological pluralism -- every translation loses something", () => {
  let f = triangle();
  for (let i = 0; i < 3; i++) f = step(f, null);
  const obs = [observer(0, 0)];
  for (const src of ["O1", "O2", "O3"]) {
    for (const tgt of ["O1", "O2", "O3"]) {
      if (src === tgt) continue;
      const t = translate(readOntology(f, src, obs), src, tgt);
      assert.ok(t.loss() > 0, `${src}->${tgt} claimed a lossless translation`);
      assert.ok(t.residue.length > 0);
    }
  }
});

test("worlds map only partially", () => {
  let f = triangle();
  for (let i = 0; i < 3; i++) f = step(f, null);
  f = step(f, new Event("new_level", [[0, 1, 2]]));
  const a = new World("a", { d0: 1000 });
  const b = new World("b", { d1: 1000 });
  const m = partialMap(f, a, b);
  const union = new Set([...a.support(f), ...b.support(f)]);
  assert.ok(m.size < union.size);
});

test("individuation records what was suppressed", () => {
  let f = Field.seed(
    ["d0"],
    8,
    [
      [0, 1, [600]],
      [1, 2, [900]],
      [2, 3, [900]],
    ],
    new Map([
      ["0,1", 600],
      ["1,2", 900],
      ["2,3", 900],
    ]),
  );
  for (let i = 0; i < 3; i++) f = step(f, null);
  const support = entities(f)[0];
  assert.deepEqual(support, [0, 1, 2, 3]);
  const [, reg] = runTracked(f, [
    {
      event: new Event("differentiate", [support]),
      observe: new Map([
        ["0,1", 300],
        ["1,2", 1350],
        ["2,3", 1350],
      ]),
    },
    null,
    null,
    null,
  ]);
  assert.ok(reg.all().some((i) => i.suppressed.length > 0));
  assert.ok(reg.all().some((i) => i.support.join(",") === "1,2,3"));
});

test("possibility is computed and non-empty on a live field", () => {
  let f = balanced();
  for (let i = 0; i < 3; i++) f = step(f, null);
  assert.ok(possibility(f).length > 0);
});

test("the specified generator and rounding rule", () => {
  assert.equal(xorshift64s(1n), 5180492295206395165n);
  assert.equal(scaleMul(-1500, 500), -750);
  assert.equal(scaleMul(1500, 500), 750);
});
