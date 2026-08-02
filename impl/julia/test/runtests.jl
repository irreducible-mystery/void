using Test
using GField

triangle() = seed(["d0"], 6,
    [(0, 1, [600]), (1, 2, [600]), (0, 2, [600])],
    Dict((0, 1) => 900, (1, 2) => 600, (0, 2) => 600))

balanced() = seed(["d0"], 6,
    [(0, 1, [600]), (1, 2, [600]), (0, 2, [600])],
    Dict((0, 1) => 600, (1, 2) => 600, (0, 2) => 600))

@testset "GField" begin

    @testset "shared corpus" begin
        passed, failures = check_all()
        @test isempty(failures) || (println(join(failures, "\n")); false)
        @test passed == length(load_corpus())
    end

    @testset "hand-written spec expectations" begin
        for vec in load_corpus()
            actual = run_vector(vec)
            hand = vec["expect"]["hand_written"]
            @test !isempty(hand)
            for (k, want) in hand
                @test actual["checks"][k] == want
            end
        end
    end

    @testset "principle 1 -- entities are a function of relations alone" begin
        f = balanced()
        for _ in 1:3
            f = advance(f)
        end
        @test entities(f) == [[0, 1, 2]]

        g = seed(["d0"], 6, Tuple{Int,Int,Vector{Int}}[])
        for _ in 1:3
            g = advance(g)
        end
        @test isempty(entities(g))
    end

    @testset "principle 5 -- the space itself can grow" begin
        f = triangle()
        @test length(f.dims) == 1
        @test residual_total(f) == 300
        for _ in 1:3
            f = advance(f)
        end
        @test length(f.dims) == 2
        @test residual_total(f) == 0
    end

    @testset "principle 5 -- a field in accord invents nothing" begin
        f = balanced()
        for _ in 1:5
            f = advance(f)
        end
        @test length(f.dims) == 1
    end

    @testset "principle 6 -- observation changes what is observed" begin
        f = balanced()
        for _ in 1:3
            f = advance(f)
        end
        before = entities(f)
        reading, g = observe_read(f, Observer(0, 100))
        @test reading > 0
        for _ in 1:3
            g = advance(g)
        end
        @test entities(g) != before
    end

    @testset "principle 6 -- a detached observer must say so, then changes nothing" begin
        f = balanced()
        for _ in 1:3
            f = advance(f)
        end
        reading, g = observe_read(f, Observer(0, 0))
        @test reading > 0
        @test digest(g) == digest(f)
    end

    @testset "ontological pluralism -- every translation loses something" begin
        f = triangle()
        for _ in 1:3
            f = advance(f)
        end
        obs = [Observer(0, 0)]
        for src in ("O1", "O2", "O3"), tgt in ("O1", "O2", "O3")
            src == tgt && continue
            t = translate(read_ontology(f, src, obs), src, tgt)
            @test loss(t) > 0
            @test !isempty(t.residue)
        end
    end

    @testset "individuation records what was suppressed" begin
        f = seed(["d0"], 8,
            [(0, 1, [600]), (1, 2, [900]), (2, 3, [900])],
            Dict((0, 1) => 600, (1, 2) => 900, (2, 3) => 900))
        for _ in 1:3
            f = advance(f)
        end
        support_ = entities(f)[1]
        @test support_ == [0, 1, 2, 3]
        obs = Dict((0, 1) => 300, (1, 2) => 1350, (2, 3) => 1350)
        _, reg = run_tracked(f, Any[(Event("differentiate", Any[support_]), obs),
                                    nothing, nothing, nothing])
        inds = GField.allof(reg)
        @test any(i -> !isempty(i.suppressed), inds)
        @test any(i -> i.support == [1, 2, 3], inds)
    end

    @testset "the specified generator and rounding rule" begin
        @test xorshift64s(UInt64(1)) == UInt64(5180492295206395165)
        @test scale_mul(-1500, 500) == -750
        @test scale_mul(1500, 500) == 750
    end

end
