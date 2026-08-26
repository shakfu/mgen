"""Validation profiles.

Two questions were previously tangled together: what a construct *means* and
whether it is *acceptable*. Feature rules answer the first and belong to the
validator. A profile answers the second, and different callers want different
answers from the same source: a conservative profile rejects anything whose type
could not be established, while a permissive one reports it and moves on.

Keeping policy here means the subset validator never has to know who is asking.
"""

from dataclasses import dataclass
from typing import Optional

# Below this, an inferred type is too weak to translate against.
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


@dataclass(frozen=True)
class StaticProfile:
    """A named validation policy."""

    name: str
    description: str
    # Whether a type that could not be established well enough is fatal.
    reject_low_confidence: bool = False
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    # Whether every non-fatal finding is promoted to a failure.
    warnings_are_errors: bool = False
    # Feature rule keys this profile refuses regardless of their declared
    # status. Backend profiles populate this from measured capability.
    rejected_features: frozenset[str] = frozenset()


PORTABLE = StaticProfile(
    name="portable",
    description=(
        "The common subset across the supported targets. Reports weakly inferred "
        "types and experimental features without failing on them."
    ),
)

# Settled by measuring generated C against CPython rather than by preference.
# See docs/supported_syntax.md and the notes on each rule.
#
# generators / yield_from: a generator can be defined but not consumed. The C
#   backend refuses `for v in counter(5)`, so the feature has no end-to-end path.
# exceptions: an explicit `raise` is caught and `finally` runs, but operations do
#   not raise. `10 // 0` inside a try dies of SIGFPE where Python returns from
#   the handler, and a handler that never fires is worse than no handler.
# context_managers: NOT rejected. The basic form was measured to execute and
#   agree with CPython, so excluding it would be caution without evidence.
STRICT_STATIC_EXCLUSIONS = frozenset({"generators", "yield_from", "exceptions"})

STRICT_STATIC = StaticProfile(
    name="strict-static",
    description=(
        "The conservative statically translatable subset. Fails on anything whose "
        "type could not be established, on any construct that is only "
        "experimentally supported, and on generators and exceptions, whose "
        "semantics the backends do not fully model."
    ),
    reject_low_confidence=True,
    warnings_are_errors=True,
    rejected_features=STRICT_STATIC_EXCLUSIONS,
)

PROFILES: dict[str, StaticProfile] = {
    PORTABLE.name: PORTABLE,
    STRICT_STATIC.name: STRICT_STATIC,
}

DEFAULT_PROFILE = PORTABLE


def _backend_profiles() -> dict[str, StaticProfile]:
    """Profiles derived from measured backend capability.

    Imported lazily: backend_capabilities imports this module for StaticProfile,
    and the registry it reads from imports the backends.
    """
    from .backend_capabilities import backend_profile, backend_profile_names

    return {name: backend_profile(name) for name in backend_profile_names()}


def profile_names() -> list[str]:
    """Names of the available profiles, in a stable order."""
    return sorted(set(PROFILES) | set(_backend_profiles()))


def get_profile(name: Optional[str]) -> StaticProfile:
    """Look up a profile by name.

    A backend name selects the profile describing what that backend can
    actually translate, as measured rather than as declared.

    Args:
        name: Profile name, backend name, or None for the default.

    Raises:
        ValueError: If no profile carries that name.
    """
    if name is None:
        return DEFAULT_PROFILE
    if name in PROFILES:
        return PROFILES[name]
    backends = _backend_profiles()
    if name in backends:
        return backends[name]
    raise ValueError(f"Unknown validation profile '{name}'. Available: {', '.join(profile_names())}")
