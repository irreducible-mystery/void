"""gfield -- a generative field.

Reference implementation of docs/spec/core.md.

Deliberately absent from this API: any function that creates an entity, any
translation that returns an image without its residue, and any predicate
meaning 'complete'. Those absences are the specification, not oversights.
"""

from .core import (COHESION, MAX_SITES, PERSISTENCE, SCALE, THETA, Field,
                   Relation, candidates, cohesion_holds, coupling, entities,
                   residual, residual_total, scale_mul, xorshift64s)
from .dynamics import (TAU, WINDOW, Individual, Registry, alternatives,
                       contradictions, generate_dimension, reducible_within_space,
                       run, run_tracked, step)
from .events import (Event, apply, becoming_accessible, bisect, enabled, gap,
                     instances, possibility, state)
from .model import Model, Revision
from .views import (ONTOLOGIES, Observer, Translation, World, partial_map,
                    read, read_ontology, shared_world, translate)

__all__ = [
    "SCALE", "THETA", "PERSISTENCE", "COHESION", "MAX_SITES", "TAU", "WINDOW",
    "Field", "Relation", "Event", "Individual", "Registry", "Model", "Revision",
    "Observer", "World", "Translation",
    "coupling", "candidates", "entities", "cohesion_holds", "residual",
    "residual_total", "scale_mul", "xorshift64s",
    "instances", "possibility", "becoming_accessible", "enabled", "gap",
    "apply", "bisect", "state",
    "step", "run", "run_tracked", "generate_dimension", "contradictions",
    "reducible_within_space", "alternatives",
    "ONTOLOGIES", "read_ontology", "translate", "partial_map", "shared_world", "read",
]

__version__ = "0.0.0"
