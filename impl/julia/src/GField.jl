"""
    GField

A generative field. Julia implementation of `docs/spec/core.md`.

Two names differ from the reference implementation to avoid shadowing `Base`:
`advance` is the spec's `step`, and `apply_event` is its `apply`. Behaviour is
identical, and the shared conformance corpus is the arbiter.

No function here creates an entity. Entities are computed from relations.
"""
module GField

using JSON

export SCALE, THETA, PERSISTENCE, COHESION, MAX_SITES, TAU, WINDOW
export Relation, Field, Event, World, Observer, Individual, Registry
export seed, copyfield, digest, coupling, candidates, entities, cohesion_holds
export residual, residual_total, all_pairs
export gap, enabled, apply_event, instances, possibility, becoming_accessible
export advance, generate_dimension, reducible_within_space, run_tracked, alternatives
export read_ontology, translate, loss, partial_map, shared_world, observe_read
export scale_mul, xorshift64s
export load_corpus, run_vector, check_all

const SCALE = 1000
const THETA = 500
const PERSISTENCE = 3
const COHESION = 600
const MAX_SITES = 64

const BOUNDARY_DECAY = 500
const REINFORCE = 1500
const JOIN_W = 700
const FEEDBACK_W = 600
const LEVEL_W = 800
const BECOMING_WINDOW = 2

const TAU = 100
const WINDOW = 3

"""v * f / SCALE, truncating toward zero (spec section 0). `div` truncates."""
scale_mul(v::Int, f::Int) = div(v * f, SCALE)

"""The generator named in spec section 0, masked to 64 bits at each step."""
function xorshift64s(seed::UInt64)
    s = seed
    s ⊻= s >> 12
    s ⊻= (s << 25)
    s ⊻= s >> 27
    return s * 0x2545F4914F6CDD1D
end

const Pair2 = Tuple{Int,Int}

struct Relation
    id::Int
    a::Int
    b::Int
    w::Vector{Int}
end

pairof(r::Relation) = (r.a, r.b)
wtotal(r::Relation) = sum(r.w; init=0)

struct EventRecord
    tick::Int
    name::String
    params::Vector{Any}
    note::String
end

mutable struct Field
    dims::Vector{String}
    sites::Int
    relations::Vector{Relation}
    observed::Dict{Pair2,Int}
    tick::Int
    history::Vector{EventRecord}
    candidate_log::Vector{Set{Vector{Int}}}
    residual_streak::Dict{Pair2,Int}
    gap_log::Vector{Dict{String,Int}}
    next_relation_id::Int
end

function seed(dims::Vector{String}, sites::Int,
              relations::Vector{<:Tuple}, observed::Dict{Pair2,Int}=Dict{Pair2,Int}())
    rels = Relation[]
    for (i, (a, b, w)) in enumerate(relations)
        a < b || error("relation endpoints must satisfy a < b, got $a,$b")
        length(w) == length(dims) || error("relation weight arity must equal length(dims)")
        push!(rels, Relation(i - 1, a, b, collect(Int, w)))
    end
    f = Field(copy(dims), sites, rels, copy(observed), 0, EventRecord[],
              Set{Vector{Int}}[], Dict{Pair2,Int}(), Dict{String,Int}[], length(rels))
    push!(f.candidate_log, Set(candidates(f)))
    push!(f.gap_log, Dict{String,Int}())
    return f
end

copyfield(f::Field) = Field(copy(f.dims), f.sites,
    [Relation(r.id, r.a, r.b, copy(r.w)) for r in f.relations],
    copy(f.observed), f.tick, copy(f.history), copy(f.candidate_log),
    copy(f.residual_streak), copy(f.gap_log), f.next_relation_id)

function add_relation!(f::Field, a::Int, b::Int, w::Vector{Int})
    a == b && error("a relation may not join a site to itself")
    lo, hi = a < b ? (a, b) : (b, a)
    push!(f.relations, Relation(f.next_relation_id, lo, hi, copy(w)))
    f.next_relation_id += 1
end

# --- derivation (spec section 2) ------------------------------------------

function coupling(f::Field)
    acc = Dict{Pair2,Int}()
    for r in f.relations
        k = pairof(r)
        acc[k] = get(acc, k, 0) + sum(abs, r.w; init=0)
    end
    return acc
end

function components(f::Field, cpl::Dict{Pair2,Int})
    parent = collect(0:(f.sites - 1))
    find(x) = begin
        while parent[x + 1] != x
            parent[x + 1] = parent[parent[x + 1] + 1]
            x = parent[x + 1]
        end
        x
    end
    for k in sort(collect(keys(cpl)))
        if cpl[k] >= THETA
            ra, rb = find(k[1]), find(k[2])
            if ra != rb
                parent[max(ra, rb) + 1] = min(ra, rb)
            end
        end
    end
    groups = Dict{Int,Vector{Int}}()
    for s in 0:(f.sites - 1)
        push!(get!(groups, find(s), Int[]), s)
    end
    return sort([sort(g) for g in values(groups) if length(g) >= 2])
end

function cohesion_holds(f::Field, support::Vector{Int})
    inside = Set(support)
    internal = 0
    boundary = 0
    for (k, c) in coupling(f)
        na, nb = k[1] in inside, k[2] in inside
        if na && nb
            internal += c
        elseif na || nb
            boundary += c
        end
    end
    return internal * SCALE >= COHESION * (internal + boundary)
end

"""Components that both hold together and clear the coupling threshold."""
candidates(f::Field) = [s for s in components(f, coupling(f)) if cohesion_holds(f, s)]

"""
Persistent convergences of relations (section 1 of the source text).
A candidate becomes an entity only by surviving unchanged for PERSISTENCE ticks.
"""
function entities(f::Field)
    length(f.candidate_log) < PERSISTENCE && return Vector{Int}[]
    recent = f.candidate_log[(end - PERSISTENCE + 1):end]
    return sort([s for s in recent[end] if all(step -> s in step, recent)])
end

# --- accountability (spec section 5) --------------------------------------

function residual(f::Field, p::Pair2)
    modeled = 0
    for r in f.relations
        pairof(r) == p && (modeled += wtotal(r))
    end
    return get(f.observed, p, 0) - modeled
end

function all_pairs(f::Field)
    s = Set{Pair2}(keys(f.observed))
    for r in f.relations
        push!(s, pairof(r))
    end
    return sort(collect(s))
end

residual_total(f::Field) = sum(p -> abs(residual(f, p)), all_pairs(f); init=0)

function digest(f::Field)
    rels = sort(f.relations, by = r -> (r.a, r.b, r.id))
    return Dict{String,Any}(
        "dims" => copy(f.dims),
        "sites" => f.sites,
        "tick" => f.tick,
        "relations" => [[r.a, r.b, copy(r.w)] for r in rels],
        "entities" => [copy(s) for s in entities(f)],
        "residual_total" => residual_total(f),
    )
end

# --- the eight rules (spec section 3) -------------------------------------

struct Event
    name::String
    params::Vector{Any}
end

"""Canonical identity, fixed across implementations (spec section 3)."""
function key(e::Event)
    parts = [p isa AbstractVector ? join(p, ",") : string(p) for p in e.params]
    return "$(e.name)($(join(parts, ";")))"
end

asset(p) = p isa AbstractVector ? Set(Int.(p)) : Set([Int(p)])

"""Canonical minimum-coupling bisection by prefix split."""
function bisect(f::Field, support::Vector{Int})
    cpl = coupling(f)
    best_k, best_cross = 1, nothing
    for k in 1:(length(support) - 1)
        left, right = Set(support[1:k]), Set(support[(k + 1):end])
        cross = 0
        for (p, c) in cpl
            if (p[1] in left && p[2] in right) || (p[1] in right && p[2] in left)
                cross += c
            end
        end
        if best_cross === nothing || cross < best_cross
            best_k, best_cross = k, cross
        end
    end
    return support[1:best_k], support[(best_k + 1):end]
end

function pair_class(r::Relation, s::Set{Int})
    na, nb = r.a in s, r.b in s
    na && nb && return :inside
    (na || nb) && return :crossing
    return :outside
end

function boundary_coupling(f::Field, s::Set{Int})
    total = 0
    for (p, c) in coupling(f)
        (p[1] in s) != (p[2] in s) && (total += c)
    end
    return total
end

"""Non-negative distance to enablement; zero exactly when the event is possible."""
function gap(f::Field, e::Event)
    p = e.params
    if e.name == "form_boundary"
        s = asset(p[1])
        return (!isempty(s) && boundary_coupling(f, s) > 0) ? 0 : 1
    elseif e.name == "differentiate"
        return max(0, 4 - length(p[1]))
    elseif e.name == "join"
        s, t = asset(p[1]), asset(p[2])
        return (!isempty(s) && !isempty(t) && isempty(intersect(s, t))) ? 0 : 1
    elseif e.name in ("branch", "repeat")
        return max(0, f.sites + length(p[1]) - MAX_SITES)
    elseif e.name == "feedback"
        return any(r -> r.a == p[1] && r.b == p[2], f.relations) ? 0 : 1
    elseif e.name == "new_level"
        return max(0, 2 - length(p[1])) + (f.sites < MAX_SITES ? 0 : 1)
    elseif e.name == "dissolve"
        s = asset(p[1])
        return any(r -> pair_class(r, s) == :inside, f.relations) ? 0 : 1
    end
    error("unknown event $(e.name)")
end

enabled(f::Field, e::Event) = gap(f, e) == 0

"""Return a new field. The only way a field state may come into being."""
function apply_event(f::Field, e::Event, note::String="")
    enabled(f, e) || error("precondition not met for $(key(e))")
    g = copyfield(f)
    p = e.params

    if e.name == "form_boundary"
        s = asset(p[1])
        g.relations = [pair_class(r, s) == :crossing ?
            Relation(r.id, r.a, r.b, [scale_mul(x, BOUNDARY_DECAY) for x in r.w]) : r
            for r in g.relations]

    elseif e.name == "differentiate"
        left, right = bisect(f, Int.(p[1]))
        ls, rs = Set(left), Set(right)
        out = Relation[]
        for r in g.relations
            crossing = (r.a in ls && r.b in rs) || (r.a in rs && r.b in ls)
            intra = (r.a in ls && r.b in ls) || (r.a in rs && r.b in rs)
            factor = crossing ? BOUNDARY_DECAY : (intra ? REINFORCE : nothing)
            push!(out, factor === nothing ? r :
                  Relation(r.id, r.a, r.b, [scale_mul(x, factor) for x in r.w]))
        end
        g.relations = out

    elseif e.name == "join"
        a, b = minimum(Int.(p[1])), minimum(Int.(p[2]))
        add_relation!(g, a, b, vcat([JOIN_W], zeros(Int, length(g.dims) - 1)))

    elseif e.name in ("branch", "repeat")
        src = Int.(p[1])
        mapping = Dict(s => g.sites + i - 1 for (i, s) in enumerate(src))
        g.sites += length(src)
        inside = Set(src)
        for r in f.relations
            cls = pair_class(r, inside)
            if cls == :inside
                add_relation!(g, mapping[r.a], mapping[r.b], copy(r.w))
            elseif cls == :crossing && e.name == "repeat"
                if r.a in inside
                    add_relation!(g, mapping[r.a], r.b, copy(r.w))
                else
                    add_relation!(g, r.a, mapping[r.b], copy(r.w))
                end
            end
        end

    elseif e.name == "feedback"
        add_relation!(g, Int(p[1]), Int(p[2]),
                      vcat([FEEDBACK_W], zeros(Int, length(g.dims) - 1)))

    elseif e.name == "new_level"
        level = g.sites
        g.sites += 1
        for m in sort(Int.(p[1]))
            add_relation!(g, m, level, vcat([LEVEL_W], zeros(Int, length(g.dims) - 1)))
        end

    elseif e.name == "dissolve"
        s = asset(p[1])
        g.relations = [r for r in g.relations if pair_class(r, s) != :inside]
    end

    push!(g.history, EventRecord(g.tick, e.name, copy(p), note))
    return g
end

"""The canonical, finite space of event instances considered at a field."""
function instances(f::Field)
    out = Event[]
    cands = candidates(f)
    for s in cands, name in ("form_boundary", "differentiate", "branch",
                             "repeat", "new_level", "dissolve")
        push!(out, Event(name, Any[s]))
    end
    for i in 1:length(cands), j in (i + 1):length(cands)
        push!(out, Event("join", Any[cands[i], cands[j]]))
    end
    pairs = sort(collect(Set(pairof(r) for r in f.relations)))
    for p in pairs
        push!(out, Event("feedback", Any[p[1], p[2]]))
    end
    return sort(out, by = key)
end

possibility(f::Field) = [e for e in instances(f) if enabled(f, e)]

"""
Events whose distance to enablement is strictly decreasing.
Our reading of 'what is becoming accessible'; tracked as contradictions/003.
"""
function becoming_accessible(f::Field)
    length(f.gap_log) < BECOMING_WINDOW + 1 && return Event[]
    window = f.gap_log[(end - BECOMING_WINDOW):end]
    out = Event[]
    for e in instances(f)
        k = key(e)
        all(step -> haskey(step, k), window) || continue
        series = [step[k] for step in window]
        if series[end] > 0 && all(i -> series[i + 1] < series[i], 1:(length(series) - 1))
            push!(out, e)
        end
    end
    return out
end

snapshot_gaps(f::Field) = Dict(key(e) => gap(f, e) for e in instances(f))

# --- dimension generation (spec section 5) --------------------------------

function reducible_within_space(f::Field)
    base = residual_total(f)
    for e in possibility(f)
        try
            residual_total(apply_event(f, e)) < base && return true
        catch
            continue
        end
    end
    return false
end

"""F_n -> F_{n+1}: add the coordinate the old space could not express."""
function generate_dimension(f::Field)
    g = copyfield(f)
    name = "d$(length(g.dims))"
    push!(g.dims, name)

    first_of_pair = Dict{Pair2,Int}()
    for r in sort(g.relations, by = r -> (r.a, r.b, r.id))
        haskey(first_of_pair, pairof(r)) || (first_of_pair[pairof(r)] = r.id)
    end

    g.relations = [Relation(r.id, r.a, r.b,
        vcat(r.w, [first_of_pair[pairof(r)] == r.id ? residual(f, pairof(r)) : 0]))
        for r in g.relations]

    covered = Set(pairof(r) for r in g.relations)
    for p in sort(collect(setdiff(Set(keys(g.observed)), covered)))
        res = residual(f, p)
        if res != 0
            add_relation!(g, p[1], p[2], vcat(zeros(Int, length(g.dims) - 1), [res]))
        end
    end

    g.residual_streak = Dict{Pair2,Int}()
    push!(g.history, EventRecord(g.tick, "dimension", Any[name],
        "persistent contradiction -> new distinction -> expanded space"))
    push!(g.history, EventRecord(g.tick, "migration", Any[name],
        "all prior records extended with coordinate $name; prior fields take 0 there"))
    return g
end

"""One tick of both dynamics (spec section 6)."""
function advance(f::Field, event::Union{Event,Nothing}=nothing,
                 observe::Union{Dict{Pair2,Int},Nothing}=nothing)
    g = event === nothing ? copyfield(f) : apply_event(f, event)
    g.tick += 1

    if observe !== nothing && !isempty(observe)
        merge!(g.observed, observe)
        push!(g.history, EventRecord(g.tick, "accountability",
            Any[sort(collect(keys(observe)))], "what the field answers to changed"))
    end

    for p in all_pairs(g)
        g.residual_streak[p] = abs(residual(g, p)) > TAU ?
            get(g.residual_streak, p, 0) + 1 : 0
    end

    persistent = any(v -> v >= WINDOW, values(g.residual_streak))
    if persistent && !reducible_within_space(g)
        g = generate_dimension(g)
    end

    push!(g.candidate_log, Set(candidates(g)))
    push!(g.gap_log, snapshot_gaps(g))
    return g
end

# --- individuation (spec section 7) ---------------------------------------

mutable struct Individual
    support::Vector{Int}
    born_at::Int
    formation_event::String
    maintained_by::Vector{Int}
    dissolution_condition::String
    suppressed::Vector{Vector{Int}}
    died_at::Union{Int,Nothing}
end

mutable struct Registry
    open::Dict{Vector{Int},Individual}
    closed::Vector{Individual}
    pending::Vector{Vector{Int}}
    pending_ttl::Int
end

Registry() = Registry(Dict{Vector{Int},Individual}(), Individual[], Vector{Int}[], 0)

function observe!(reg::Registry, f::Field, formation_event::String="seed",
                  suppressed::Vector{Vector{Int}}=Vector{Int}[])
    if !isempty(suppressed)
        reg.pending = [copy(s) for s in suppressed]
        reg.pending_ttl = PERSISTENCE + 1
    end
    present = Set(entities(f))
    born = sort([s for s in present if !haskey(reg.open, s)])

    for support in born
        inside = Set(support)
        reg.open[support] = Individual(copy(support), f.tick, formation_event,
            sort([r.id for r in f.relations if r.a in inside && r.b in inside]),
            "coupling below THETA",
            reg.pending_ttl > 0 ? [copy(s) for s in reg.pending] : Vector{Int}[],
            nothing)
    end
    if !isempty(born) && reg.pending_ttl > 0
        reg.pending, reg.pending_ttl = Vector{Int}[], 0
    elseif reg.pending_ttl > 0
        reg.pending_ttl -= 1
    end

    for support in sort([s for s in keys(reg.open) if !(s in present)])
        ind = reg.open[support]
        delete!(reg.open, support)
        ind.died_at = f.tick
        push!(reg.closed, ind)
    end
end

allof(reg::Registry) = sort(vcat(reg.closed, collect(values(reg.open))),
                            by = i -> (i.born_at, i.support))

"""Every viable bisection of a support, so the unchosen ones can be recorded."""
function alternatives(f::Field, support::Vector{Int})
    chosen, _ = bisect(f, support)
    return [support[1:k] for k in 1:(length(support) - 1) if support[1:k] != chosen]
end

function run_tracked(f::Field, schedule::Vector)
    reg = Registry()
    observe!(reg, f)
    g = f
    for item in schedule
        e, obs = item isa Tuple ? item : (item, nothing)
        suppressed = (e !== nothing && e.name == "differentiate") ?
            alternatives(g, Int.(e.params[1])) : Vector{Int}[]
        g = advance(g, e, obs)
        observe!(reg, g, e === nothing ? "drift" : e.name, suppressed)
    end
    return g, reg
end

# --- ontologies, worlds, observers (spec sections 8-10) -------------------

const ONTOLOGIES = Dict("O1" => ("objects", "properties", "causes"),
                        "O2" => ("processes", "relations", "constraints"),
                        "O3" => ("agents", "meanings", "purposes"))

struct Observer
    site::Int
    back_action::Int
end

function read_ontology(f::Field, name::String, observers::Vector{Observer}=Observer[])
    terms = String[]
    obs = sort(observers, by = o -> o.site)
    pairs = sort(collect(Set(pairof(r) for r in f.relations)))
    if name == "O1"
        append!(terms, ["object:" * join(s, "-") for s in entities(f)])
        append!(terms, ["property:$d" for d in f.dims])
        append!(terms, ["cause:$(p[1])-$(p[2])" for p in pairs])
    elseif name == "O2"
        append!(terms, ["process:$n" for n in sort(collect(Set(h.name for h in f.history)))])
        append!(terms, ["relation:$(p[1])-$(p[2])" for p in pairs])
        append!(terms, ["constraint:$n" for n in sort(collect(Set(e.name for e in instances(f))))])
    elseif name == "O3"
        append!(terms, ["agent:$(o.site)" for o in obs])
        append!(terms, ["meaning:$(o.site)" for o in obs])
        inst = instances(f)
        append!(terms, ["purpose:$(key(e))" for e in inst[1:min(1, length(inst))]])
    else
        error("unknown ontology $name")
    end
    return terms
end

const CORRESPONDENCE = Dict(
    ("O1", "O2") => Dict("object" => "process", "cause" => "relation", "property" => nothing),
    ("O2", "O1") => Dict("process" => "object", "relation" => "cause", "constraint" => nothing),
    ("O1", "O3") => Dict("object" => "agent", "property" => "meaning", "cause" => nothing),
    ("O3", "O1") => Dict("agent" => "object", "meaning" => "property", "purpose" => nothing),
    ("O2", "O3") => Dict("process" => "purpose", "relation" => "meaning", "constraint" => nothing),
    ("O3", "O2") => Dict("meaning" => "relation", "purpose" => "process", "agent" => nothing),
)

struct Translation
    source::String
    target::String
    image::Vector{String}
    residue::Vector{String}
end

function loss(t::Translation)
    total = length(t.image) + length(t.residue)
    total == 0 && return 0
    return div(length(t.residue) * SCALE, total)
end

"""
F : O_i -> O_j, returning both the translation and its residue.
There is deliberately no variant that returns the image alone.
"""
function translate(terms::Vector{String}, source::String, target::String)
    table = CORRESPONDENCE[(source, target)]
    image, residue = String[], String[]
    for t in terms
        idx = findfirst(==(':'), t)
        kind = idx === nothing ? t : t[1:(idx - 1)]
        rest = idx === nothing ? "" : t[(idx + 1):end]
        mapped = get(table, kind, nothing)
        mapped === nothing ? push!(residue, t) : push!(image, "$mapped:$rest")
    end
    return Translation(source, target, image, residue)
end

struct World
    name::String
    relevance::Dict{String,Int}
end

function support(f::Field, w::World)
    live = Set(i for (i, d) in enumerate(f.dims) if get(w.relevance, d, 0) != 0)
    sites = Set{Int}()
    for r in f.relations
        if any(i -> i in live && r.w[i] != 0, 1:length(r.w))
            push!(sites, r.a); push!(sites, r.b)
        end
    end
    return sort(collect(sites))
end

"""Defined only where both worlds have purchase; elsewhere absent, never defaulted."""
function partial_map(f::Field, wi::World, wj::World)
    si, sj = Set(support(f, wi)), Set(support(f, wj))
    return Dict(s => s for s in sort(collect(intersect(si, sj))))
end

function shared_world(f::Field, wi::World, wj::World, name::String)
    rel = Dict{String,Int}()
    for d in f.dims
        v = min(get(wi.relevance, d, 0), get(wj.relevance, d, 0))
        v != 0 && (rel[d] = v)
    end
    return World(name, rel)
end

"""Measure, and in measuring, change what was measured."""
function observe_read(f::Field, o::Observer)
    reading = 0
    for (p, c) in coupling(f)
        (p[1] == o.site || p[2] == o.site) && (reading += c)
    end
    o.back_action == 0 && return reading, f

    g = copyfield(f)
    g.relations = [(r.a == o.site || r.b == o.site) ?
        Relation(r.id, r.a, r.b, [scale_mul(x, o.back_action) for x in r.w]) : r
        for r in g.relations]
    push!(g.history, EventRecord(g.tick, "observation", Any[o.site],
                                 "back_action=$(o.back_action)"))
    return reading, g
end

include("conformance.jl")

end # module
