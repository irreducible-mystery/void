# Runner for the shared conformance corpus.
# Mirrors impl/python/gfield/conformance.py.

"""Search upward for the corpus, so this works regardless of where Julia was started."""
function corpus_dir()
    dir = @__DIR__
    for _ in 1:8
        candidate = joinpath(dir, "conformance", "vectors")
        isdir(candidate) && return candidate
        parent = dirname(dir)
        parent == dir && break
        dir = parent
    end
    error("conformance/vectors not found above $(@__DIR__)")
end

function load_corpus(dir::String=corpus_dir())
    files = sort([f for f in readdir(dir) if endswith(f, ".json")])
    return [JSON.parsefile(joinpath(dir, f)) for f in files]
end

parse_pair(s::AbstractString) = (parse(Int, split(s, ",")[1]), parse(Int, split(s, ",")[2]))

to_observed(o) = o === nothing ? Dict{Pair2,Int}() :
    Dict{Pair2,Int}(parse_pair(k) => Int(v) for (k, v) in o)

function build(s)
    rels = [(Int(r[1]), Int(r[2]), Int.(r[3])) for r in s["relations"]]
    return seed(String.(s["dims"]), Int(s["sites"]), rels, to_observed(get(s, "observed", nothing)))
end

function run_vector(vec)
    f = build(vec["seed"])
    for entry in get(vec, "schedule", [])
        e, obs = nothing, nothing
        if entry !== nothing
            name = get(entry, "name", nothing)
            if name !== nothing
                params = Any[p isa AbstractVector ? Int.(p) : Int(p) for p in entry["params"]]
                e = Event(String(name), params)
            end
            haskey(entry, "observe") && (obs = to_observed(entry["observe"]))
        end
        f = advance(f, e, obs)
    end

    d = digest(f)
    checks = Dict{String,Any}(
        "dimension_count" => length(f.dims),
        "residual_total" => d["residual_total"],
        "entity_count" => length(entities(f)),
        "accessible_count" => length(possibility(f)),
        "becoming_count" => length(becoming_accessible(f)),
        "generated_dimension" => any(h -> h.name == "dimension", f.history),
        "history_complete" => all(h -> h.tick <= f.tick, f.history),
    )

    if get(vec, "check_translation", false)
        obs = [Observer(0, 0)]
        losses = Dict{String,Any}()
        for src in ("O1", "O2", "O3"), tgt in ("O1", "O2", "O3")
            src == tgt && continue
            losses["$src->$tgt"] = loss(translate(read_ontology(f, src, obs), src, tgt))
        end
        checks["translation_losses"] = losses
        checks["all_losses_positive"] = all(v -> v > 0, values(losses))
    end

    if haskey(vec, "check_observer")
        spec = vec["check_observer"]
        before = [copy(s) for s in entities(f)]
        _, g = observe_read(f, Observer(Int(spec["site"]), Int(spec["back_action"])))
        for _ in 1:3
            g = advance(g, nothing, nothing)
        end
        after = [copy(s) for s in entities(g)]
        checks["entities_before_observation"] = before
        checks["entities_after_observation"] = after
        checks["observation_changed_field"] = before != after
    end

    if haskey(vec, "check_worlds")
        spec = vec["check_worlds"]
        mk(w) = World(String(w["name"]), Dict{String,Int}(String(k) => Int(v) for (k, v) in w["relevance"]))
        wi, wj = mk(spec["a"]), mk(spec["b"])
        m = partial_map(f, wi, wj)
        union_size = length(union(Set(support(f, wi)), Set(support(f, wj))))
        checks["world_a_support"] = support(f, wi)
        checks["world_b_support"] = support(f, wj)
        checks["partial_map_domain"] = sort(collect(keys(m)))
        checks["map_is_partial"] = length(m) < union_size
    end

    return Dict("digest" => d, "checks" => checks)
end

"""Order-insensitive structural equality, so key order never causes a false failure."""
function canon(v)
    if v isa AbstractDict
        return "{" * join([repr(String(k)) * ":" * canon(v[k]) for k in sort(String.(collect(keys(v))))], ",") * "}"
    elseif v isa AbstractVector
        return "[" * join([canon(x) for x in v], ",") * "]"
    elseif v isa Bool
        return string(v)
    elseif v isa Integer
        return string(v)
    elseif v isa AbstractFloat
        return isinteger(v) ? string(Int(v)) : string(v)
    elseif v isa AbstractString
        return repr(String(v))
    elseif v === nothing
        return "null"
    end
    return string(v)
end

function compare(expected, actual)
    failures = String[]
    if haskey(expected, "digest")
        e, a = expected["digest"], actual["digest"]
        for k in sort(unique(vcat(String.(collect(keys(e))), String.(collect(keys(a))))))
            ce = haskey(e, k) ? canon(e[k]) : "null"
            ca = haskey(a, k) ? canon(a[k]) : "null"
            ce != ca && push!(failures, "digest.$k: expected $ce, got $ca")
        end
    end
    if haskey(expected, "checks")
        for (k, want) in expected["checks"]
            got = get(actual["checks"], k, nothing)
            canon(want) != canon(got) &&
                push!(failures, "checks.$k: expected $(canon(want)), got $(canon(got))")
        end
    end
    return failures
end

function check_all(dir::String=corpus_dir())
    passed, failures = 0, String[]
    for vec in load_corpus(dir)
        problems = compare(vec["expect"], run_vector(vec))
        if isempty(problems)
            passed += 1
        else
            append!(failures, ["[$(vec["id"])] $p" for p in problems])
        end
    end
    return passed, failures
end
