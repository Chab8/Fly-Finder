"""Controlled vocabularies shared by the catalog, the AI contracts and the API.

Values are stable codes (English, snake_case). Human-readable labels in each language
live in the mobile app's localization files, never in the database.
"""

from enum import Enum


class TaxonRank(str, Enum):
    kingdom = "kingdom"
    phylum = "phylum"
    class_ = "class"
    subclass = "subclass"
    order = "order"
    suborder = "suborder"
    infraorder = "infraorder"
    superfamily = "superfamily"
    family = "family"
    subfamily = "subfamily"
    genus = "genus"
    species = "species"
    subspecies = "subspecies"
    other = "other"


# Lower number = broader rank. Used to compare how specific an identification is.
RANK_LEVEL: dict[TaxonRank, int] = {
    TaxonRank.kingdom: 0,
    TaxonRank.phylum: 1,
    TaxonRank.class_: 2,
    TaxonRank.subclass: 3,
    TaxonRank.order: 4,
    TaxonRank.suborder: 5,
    TaxonRank.infraorder: 6,
    TaxonRank.superfamily: 7,
    TaxonRank.family: 8,
    TaxonRank.subfamily: 9,
    TaxonRank.genus: 10,
    TaxonRank.species: 11,
    TaxonRank.subspecies: 12,
    TaxonRank.other: -1,
}


class OrganismGroup(str, Enum):
    aquatic_insect = "aquatic_insect"
    terrestrial_insect = "terrestrial_insect"
    crustacean = "crustacean"
    annelid = "annelid"
    mollusc = "mollusc"
    fish = "fish"
    other = "other"


class Habitat(str, Enum):
    freshwater_running = "freshwater_running"
    freshwater_still = "freshwater_still"
    estuarine = "estuarine"
    marine = "marine"
    terrestrial = "terrestrial"


class LifeStage(str, Enum):
    egg = "egg"
    larva = "larva"
    nymph = "nymph"
    pupa = "pupa"
    emerger = "emerger"
    subimago = "subimago"
    imago = "imago"
    adult = "adult"
    juvenile = "juvenile"
    other = "other"
    unknown = "unknown"


class FlyCategory(str, Enum):
    dry_fly = "dry_fly"
    nymph = "nymph"
    emerger = "emerger"
    wet_fly = "wet_fly"
    streamer = "streamer"
    terrestrial = "terrestrial"
    saltwater = "saltwater"
    attractor = "attractor"
    other = "other"


class FishingEnvironment(str, Enum):
    freshwater = "freshwater"
    saltwater = "saltwater"
    brackish = "brackish"


class MatchType(str, Enum):
    exact_imitation = "exact_imitation"
    general_imitation = "general_imitation"
    suggestive_imitation = "suggestive_imitation"
    attractor = "attractor"
    not_specified = "not_specified"


class BiologicalCompatibility(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"


class VerificationStatus(str, Enum):
    """How much a catalog record has been checked.

    unverified       drafted from general references, needs review
    source_verified  checked against an authoritative source (e.g. GBIF backbone)
    expert_verified  reviewed and approved by a named expert
    """

    unverified = "unverified"
    source_verified = "source_verified"
    expert_verified = "expert_verified"


class PermissionStatus(str, Enum):
    approved = "approved"
    pending = "pending"
    rejected = "rejected"


class AvailabilityStatus(str, Enum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"
    preorder = "preorder"
    discontinued = "discontinued"
    unknown = "unknown"


class IdentificationKind(str, Enum):
    organism = "organism"
    fly = "fly"
