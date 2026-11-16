"""Deterministic semantic vector embedding engine for pgvector hybrid search.

Produces L2-normalized 64-dimensional float vectors combining:
- Dimensions 0..15: Multi-lingual (English / Shona / Ndebele) trade & domain
  concept clusters (plumbing, electrical, solar, welding, building, tiling,
  roofing, painting, carpentry, appliance repair, gardening, maintenance,
  urgency, installation, fault/repair, and spatial context).
- Dimensions 16..63: Signed feature hashing (Weinberger et al.) over word
  stems, word bigrams, and character 3-grams for typo tolerance and lexical
  recall.

Because embeddings are deterministic and self-contained, `pgvector` cosine
distance (`<=>`) works identically in offline/low-connectivity deployments,
CI pipelines, and local development without external API keys or network calls.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.shared_kernel.enums import TradeEnum

EMBEDDING_DIM = 64
_CONCEPT_DIMS = 16
_HASH_DIMS = EMBEDDING_DIM - _CONCEPT_DIMS

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "at",
        "be",
        "by",
        "can",
        "do",
        "for",
        "from",
        "have",
        "help",
        "i",
        "in",
        "is",
        "it",
        "job",
        "jobs",
        "looking",
        "me",
        "my",
        "need",
        "needed",
        "of",
        "on",
        "or",
        "please",
        "someone",
        "that",
        "the",
        "this",
        "to",
        "want",
        "we",
        "with",
        "work",
        "worker",
    }
)

# 16 semantic concept clusters (dims 0..15)
_CONCEPT_CLUSTERS: tuple[tuple[str, ...], ...] = (
    # 0: PLUMBING & water systems (English + Shona + Ndebele)
    (
        "plumb",
        "plumber",
        "plumbing",
        "pipe",
        "pipes",
        "tap",
        "taps",
        "leak",
        "leaking",
        "geyser",
        "toilet",
        "cistern",
        "flush",
        "drain",
        "blocked",
        "blockage",
        "sink",
        "basin",
        "shower",
        "bath",
        "borehole",
        "tank",
        "jojo",
        "water",
        "valve",
        "sewer",
        "drip",
        "dripping",
        "burst",
        "mvura",
        "yemvura",
        "pombi",
        "chimbuzi",
        "muchimbuzi",
        "donha",
        "kudonha",
        "amanzi",
    ),
    # 1: ELECTRICAL & power systems
    (
        "electric",
        "electrical",
        "electrician",
        "wire",
        "wiring",
        "rewire",
        "socket",
        "plug",
        "light",
        "lights",
        "bulb",
        "switch",
        "breaker",
        "mcb",
        "trip",
        "tripping",
        "db",
        "board",
        "power",
        "shock",
        "spark",
        "fuse",
        "cable",
        "meter",
        "zesa",
        "earth",
        "magetsi",
        "getsi",
        "ugesi",
    ),
    # 2: SOLAR & backup energy
    (
        "solar",
        "panel",
        "panels",
        "inverter",
        "battery",
        "batteries",
        "lithium",
        "mppt",
        "charge",
        "charger",
        "pv",
        "sun",
        "backup",
        "changeover",
        "zuva",
    ),
    # 3: WELDING & steelwork
    (
        "weld",
        "welder",
        "welding",
        "gate",
        "sliding",
        "burglar",
        "bars",
        "screen",
        "metal",
        "steel",
        "iron",
        "frame",
        "hinge",
        "braai",
        "palisade",
        "carport",
        "fabricate",
        "fabrication",
        "window",
        "simbi",
    ),
    # 4: BUILDING & masonry
    (
        "build",
        "builder",
        "building",
        "construction",
        "brick",
        "bricks",
        "bricklayer",
        "wall",
        "plaster",
        "plastering",
        "cement",
        "concrete",
        "foundation",
        "crack",
        "lintel",
        "slab",
        "extension",
        "durawall",
        "precast",
        "mortar",
        "dhaka",
        "chidhinha",
        "akha",
    ),
    # 5: TILING & flooring
    (
        "tile",
        "tiles",
        "tiler",
        "tiling",
        "retile",
        "grout",
        "porcelain",
        "ceramic",
        "floor",
        "flooring",
        "skirting",
        "mosaic",
    ),
    # 6: ROOFING, ceiling & gutters
    (
        "roof",
        "roofer",
        "roofing",
        "gutter",
        "gutters",
        "ceiling",
        "asbestos",
        "ibr",
        "sheeting",
        "truss",
        "fascia",
        "barge",
        "thatch",
        "denga",
    ),
    # 7: PAINTING & surface finishing
    (
        "paint",
        "painter",
        "painting",
        "repaint",
        "coat",
        "primer",
        "varnish",
        "rhinolite",
        "skim",
        "skimming",
        "peeling",
        "damp",
        "undercoat",
        "pendi",
    ),
    # 8: CARPENTRY, wood & doors
    (
        "carpenter",
        "carpentry",
        "wood",
        "wooden",
        "timber",
        "door",
        "doors",
        "cupboard",
        "wardrobe",
        "cabinet",
        "shelf",
        "shelves",
        "lock",
        "handle",
        "formica",
        "joinery",
        "deck",
        "mapuranga",
    ),
    # 9: APPLIANCE_REPAIR & white goods
    (
        "appliance",
        "appliances",
        "repair",
        "fridge",
        "freezer",
        "refrigerator",
        "stove",
        "oven",
        "plate",
        "washing",
        "machine",
        "microwave",
        "kettle",
        "iron",
        "element",
        "thermostat",
        "compressor",
        "cooling",
        "defrost",
    ),
    # 10: GARDENING & outdoor
    (
        "garden",
        "gardener",
        "gardening",
        "lawn",
        "grass",
        "mow",
        "mowing",
        "slash",
        "slashing",
        "tree",
        "trees",
        "prune",
        "branches",
        "hedge",
        "flower",
        "flowers",
        "weeding",
        "yard",
        "trench",
        "dig",
        "digging",
        "bindu",
        "uswa",
    ),
    # 11: GENERAL_MAINTENANCE & odd jobs
    (
        "handyman",
        "maintenance",
        "maintain",
        "mount",
        "hang",
        "curtain",
        "rail",
        "blind",
        "blinds",
        "general",
        "odd",
        "fix",
        "repair",
    ),
    # 12: Urgency / emergency signal
    (
        "today",
        "urgent",
        "emergency",
        "now",
        "immediately",
        "asap",
        "burst",
        "flooding",
        "sparking",
        "nhasi",
    ),
    # 13: Installation / new build signal
    (
        "install",
        "installation",
        "installing",
        "new",
        "fit",
        "fitting",
        "mount",
        "setup",
        "build",
        "construct",
        "supply",
        "extend",
    ),
    # 14: Fault / diagnostic / repair signal
    (
        "broken",
        "leak",
        "leaking",
        "fault",
        "faulty",
        "stopped",
        "working",
        "tripping",
        "beeping",
        "noisy",
        "smell",
        "damaged",
        "replace",
        "fix",
        "repair",
        "cracked",
    ),
    # 15: Household room / spatial context
    (
        "kitchen",
        "bathroom",
        "toilet",
        "lounge",
        "bedroom",
        "outside",
        "yard",
        "roof",
        "driveway",
        "gate",
        "wall",
        "house",
    ),
)

_TRADE_TO_CLUSTER: dict[TradeEnum, tuple[int, ...]] = {
    TradeEnum.PLUMBING: (0,),
    TradeEnum.ELECTRICAL: (1,),
    TradeEnum.SOLAR: (2, 1),
    TradeEnum.WELDING: (3,),
    TradeEnum.BUILDING: (4, 5, 6, 7),
    TradeEnum.TILING: (5, 4),
    TradeEnum.ROOFING: (6, 4),
    TradeEnum.PAINTING: (7, 4),
    TradeEnum.CARPENTRY: (8, 4),
    TradeEnum.APPLIANCE_REPAIR: (9, 1),
    TradeEnum.GARDENING: (10,),
    TradeEnum.GENERAL_MAINTENANCE: (11,),
}


def _stem(word: str) -> str:
    if len(word) > 5 and word.endswith("ing"):
        base = word[:-3]
        if len(base) >= 3 and base[-1] == base[-2]:
            base = base[:-1]
        return base
    if len(word) > 4 and word.endswith("ers"):
        return word[:-3]
    if len(word) > 4 and word.endswith("er"):
        return word[:-2]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if len(w) >= 2 and w not in _STOP_WORDS]


def _hash_feature(feature: str, weight: float, vector: list[float]) -> None:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    bucket = _CONCEPT_DIMS + (int.from_bytes(digest[:4], "little") % _HASH_DIMS)
    sign = 1.0 if (digest[4] & 1) == 0 else -1.0
    vector[bucket] += sign * weight


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm < 1e-9:
        fallback = [0.0] * EMBEDDING_DIM
        fallback[0] = 1.0
        return fallback
    return [round(v / norm, 6) for v in vector]


def embed_text(
    text: str | None,
    *,
    trade: TradeEnum | str | None = None,
    suburb: str | None = None,
) -> list[float]:
    """Generate a normalized 64-dimensional semantic vector for pgvector storage/query."""
    vector = [0.0] * EMBEDDING_DIM
    combined = (text or "").strip()

    # Trade prior boost when trade is known (e.g. when indexing a Job row)
    if trade is not None:
        trade_enum: TradeEnum | None = None
        if isinstance(trade, TradeEnum):
            trade_enum = trade
        else:
            try:
                trade_enum = TradeEnum(str(trade).upper())
            except ValueError:
                trade_enum = None
        if trade_enum is not None:
            clusters = _TRADE_TO_CLUSTER.get(trade_enum, ())
            for idx, cluster_id in enumerate(clusters):
                vector[cluster_id] += 2.2 if idx == 0 else 0.9
            _hash_feature(f"trade:{trade_enum.value.lower()}", 1.5, vector)

    if suburb:
        _hash_feature(f"suburb:{suburb.strip().lower()}", 0.6, vector)

    tokens = _tokenize(combined)
    stems = [_stem(tok) for tok in tokens]
    token_set = set(tokens) | set(stems)

    # 1. Concept cluster activations (dims 0..15)
    for cluster_idx, keywords in enumerate(_CONCEPT_CLUSTERS):
        hits = 0.0
        for kw in keywords:
            kw_stem = _stem(kw)
            if kw in token_set or kw_stem in token_set:
                hits += 1.0
            else:
                # Prefix match for partial words (e.g., "electr" -> "electrician")
                if any(
                    (len(tok) >= 4 and (tok.startswith(kw_stem) or kw_stem.startswith(tok)))
                    for tok in token_set
                ):
                    hits += 0.65
        if hits > 0:
            vector[cluster_idx] += math.log1p(hits) * 2.5

    # 2. Lexical + stem + bigram + character trigram hashing (dims 16..63)
    for tok, stem in zip(tokens, stems, strict=False):
        _hash_feature(f"w:{tok}", 1.0, vector)
        if stem != tok:
            _hash_feature(f"s:{stem}", 1.2, vector)
        if len(tok) >= 3:
            padded = f"^{tok}$"
            for i in range(len(padded) - 2):
                _hash_feature(f"g:{padded[i : i + 3]}", 0.35, vector)

    for i in range(len(stems) - 1):
        _hash_feature(f"bi:{stems[i]}_{stems[i + 1]}", 0.85, vector)

    return _normalize(vector)


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity in [-1.0, 1.0] between two normalized vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    return max(-1.0, min(1.0, float(dot)))


RELEVANCE_THRESHOLD = 0.12
LEXICAL_BOOST = 0.15


def relevance_score(
    query: str,
    similarity: float,
    *,
    description: str | None = None,
    suburb: str | None = None,
    trade: str | None = None,
) -> float:
    """Single, shared query-match score: vector similarity plus a lexical
    substring boost, capped at 1.0. Used by every job-matching code path
    (open-job listing, hybrid search) so results are ranked/filtered
    consistently no matter which endpoint computed them.
    """
    lower_q = query.strip().lower()
    haystacks = (description or "", suburb or "", trade or "")
    lexical_boost = LEXICAL_BOOST if any(lower_q in h.lower() for h in haystacks if h) else 0.0
    return min(1.0, round(similarity + lexical_boost, 4))


@dataclass(frozen=True)
class SkillCatalogueEntry:
    id: str
    label: str
    trade: TradeEnum | None
    category: str
    description: str


@dataclass(frozen=True)
class SkillSemanticMatch:
    id: str
    label: str
    trade: TradeEnum | None
    category: str
    similarity_score: float


SKILL_CATALOGUE: tuple[SkillCatalogueEntry, ...] = (
    SkillCatalogueEntry(
        id="plumber",
        label="Plumber",
        trade=TradeEnum.PLUMBING,
        category="Home & building",
        description=(
            "Plumber plumbing pipe tap leak leaking geyser toilet flush drain blocked sink "
            "basin shower borehole water tank valve burst mvura pombi chimbuzi"
        ),
    ),
    SkillCatalogueEntry(
        id="electrician",
        label="Electrician",
        trade=TradeEnum.ELECTRICAL,
        category="Home & building",
        description=(
            "Electrician electrical wiring wire socket plug light bulb switch breaker tripping "
            "db board power zesa fuse cable magetsi ugesi"
        ),
    ),
    SkillCatalogueEntry(
        id="bricklayer",
        label="Bricklayer",
        trade=TradeEnum.BUILDING,
        category="Home & building",
        description=(
            "Bricklayer builder building brick wall plaster cement concrete foundation crack "
            "slab extension durawall dhaka chidhinha"
        ),
    ),
    SkillCatalogueEntry(
        id="tiler",
        label="Tiler",
        trade=TradeEnum.BUILDING,
        category="Home & building",
        description="Tiler tiling tile retile floor bathroom kitchen grout porcelain ceramic",
    ),
    SkillCatalogueEntry(
        id="roof-leak",
        label="Roof leak repair",
        trade=TradeEnum.BUILDING,
        category="Home & building",
        description="Roof leak repair roofing gutter ceiling asbestos ibr sheeting truss denga",
    ),
    SkillCatalogueEntry(
        id="painter",
        label="Painter",
        trade=TradeEnum.BUILDING,
        category="Home & building",
        description="Painter painting paint repaint wall coat primer varnish rhinolite skimming",
    ),
    SkillCatalogueEntry(
        id="welder",
        label="Welder",
        trade=TradeEnum.WELDING,
        category="Home & building",
        description=(
            "Welder welding weld sliding gate burglar bars metal steel iron frame hinge "
            "palisade carport fabrication window simbi"
        ),
    ),
    SkillCatalogueEntry(
        id="solar",
        label="Solar installer",
        trade=TradeEnum.SOLAR,
        category="Home & building",
        description=(
            "Solar installer panel panels inverter battery lithium mppt charge backup power zuva"
        ),
    ),
    SkillCatalogueEntry(
        id="appliance",
        label="Appliance repair",
        trade=TradeEnum.APPLIANCE_REPAIR,
        category="Home & building",
        description=(
            "Appliance repair fridge freezer refrigerator stove oven plate washing machine "
            "microwave kettle iron element thermostat cooling"
        ),
    ),
    SkillCatalogueEntry(
        id="gardener",
        label="Gardener",
        trade=None,
        category="Outdoor & farm",
        description="Gardener gardening garden hedge flowers lawn weeding yard bindu",
    ),
    SkillCatalogueEntry(
        id="grass-cutter",
        label="Grass cutter",
        trade=None,
        category="Outdoor & farm",
        description="Grass cutter lawn mowing mower slashing yard uswa",
    ),
    SkillCatalogueEntry(
        id="tree-cutter",
        label="Tree cutter",
        trade=None,
        category="Outdoor & farm",
        description="Tree cutter trees branches pruning",
    ),
    SkillCatalogueEntry(
        id="farm-worker",
        label="Farm worker",
        trade=None,
        category="Outdoor & farm",
        description="Farm worker farming crops planting harvest",
    ),
    SkillCatalogueEntry(
        id="trencher",
        label="Trencher",
        trade=None,
        category="Outdoor & farm",
        description="Trencher trench digging dig",
    ),
    SkillCatalogueEntry(
        id="house-help",
        label="House help",
        trade=None,
        category="Care & household",
        description="House help cleaning clean housework maid",
    ),
    SkillCatalogueEntry(
        id="baby-sitter",
        label="Baby sitter",
        trade=None,
        category="Care & household",
        description="Baby sitter babysitting child children nanny",
    ),
    SkillCatalogueEntry(
        id="laundry",
        label="Laundry",
        trade=None,
        category="Care & household",
        description="Laundry washing ironing clothes",
    ),
    SkillCatalogueEntry(
        id="dog-walker",
        label="Dog walker",
        trade=None,
        category="Care & household",
        description="Dog walker dogs pets",
    ),
    SkillCatalogueEntry(
        id="school-run",
        label="School run driver",
        trade=None,
        category="Care & household",
        description="School run driver driving transport",
    ),
    SkillCatalogueEntry(
        id="mechanic",
        label="Motor mechanic",
        trade=None,
        category="Vehicles",
        description="Motor mechanic car engine vehicle service",
    ),
    SkillCatalogueEntry(
        id="panel-beater",
        label="Panel beater",
        trade=None,
        category="Vehicles",
        description="Panel beater dent spray body",
    ),
    SkillCatalogueEntry(
        id="car-washer",
        label="Car washer",
        trade=None,
        category="Vehicles",
        description="Car washer wash valet",
    ),
)

_SKILL_EMBEDDINGS: dict[str, list[float]] = {
    entry.id: embed_text(entry.description, trade=entry.trade) for entry in SKILL_CATALOGUE
}


def rank_skills_by_query(query: str, *, limit: int = 10) -> list[SkillSemanticMatch]:
    """Rank skills against a natural-language query using vector cosine similarity."""
    cleaned = query.strip()
    if not cleaned:
        return []
    q_vec = embed_text(cleaned)
    scored: list[SkillSemanticMatch] = []
    for entry in SKILL_CATALOGUE:
        sim = cosine_similarity(q_vec, _SKILL_EMBEDDINGS[entry.id])
        if sim >= 0.15:
            scored.append(
                SkillSemanticMatch(
                    id=entry.id,
                    label=entry.label,
                    trade=entry.trade,
                    category=entry.category,
                    similarity_score=round(sim, 4),
                )
            )
    scored.sort(key=lambda item: (-item.similarity_score, item.trade is None))
    return scored[:limit]


def infer_best_trade(query: str) -> tuple[TradeEnum | None, float]:
    """Return the top selectable TradeEnum and its similarity score for a query."""
    matches = rank_skills_by_query(query, limit=5)
    for match in matches:
        if match.trade is not None:
            return match.trade, match.similarity_score
    return None, 0.0
