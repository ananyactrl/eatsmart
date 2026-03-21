"""
Regulatory Knowledge Base for EatSmartly.

Structured database of food additives, ingredients, and their regulatory status
across FSSAI (India), FDA (USA), EFSA (EU), and CODEX Alimentarius.

Every piece of information is source-cited. We don't make claims — we aggregate
what regulators, researchers, and public databases already say.
"""
import json
import os
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class RegulatoryBody(str, Enum):
    FSSAI = "FSSAI"          # Food Safety and Standards Authority of India
    FDA = "FDA"              # US Food and Drug Administration
    EFSA = "EFSA"            # European Food Safety Authority
    CODEX = "CODEX"          # Codex Alimentarius (WHO/FAO)
    JECFA = "JECFA"          # Joint FAO/WHO Expert Committee on Food Additives
    WHO = "WHO"


class ApprovalStatus(str, Enum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITS = "approved_with_limits"
    BANNED = "banned"
    RESTRICTED = "restricted"
    UNDER_REVIEW = "under_review"
    NOT_EVALUATED = "not_evaluated"
    GRAS = "gras"            # Generally Recognized As Safe (FDA)


class IngredientCategory(str, Enum):
    PRESERVATIVE = "preservative"
    COLORANT = "colorant"
    SWEETENER = "sweetener"
    EMULSIFIER = "emulsifier"
    STABILIZER = "stabilizer"
    THICKENER = "thickener"
    FLAVOR_ENHANCER = "flavor_enhancer"
    ANTIOXIDANT = "antioxidant"
    ACIDITY_REGULATOR = "acidity_regulator"
    RAISING_AGENT = "raising_agent"
    ANTI_CAKING_AGENT = "anti_caking_agent"
    HUMECTANT = "humectant"
    SEQUESTRANT = "sequestrant"
    FLOUR_TREATMENT = "flour_treatment"
    GLAZING_AGENT = "glazing_agent"
    PROPELLANT = "propellant"
    BULKING_AGENT = "bulking_agent"
    CARRIER = "carrier"
    NATURAL_INGREDIENT = "natural_ingredient"
    SUGAR = "sugar"
    FAT_OIL = "fat_oil"
    GRAIN_FLOUR = "grain_flour"
    OTHER = "other"


class ConcernLevel(str, Enum):
    """How much concern exists in peer-reviewed literature."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CONTROVERSIAL = "controversial"  # Conflicting evidence


@dataclass
class Source:
    """A citable source for any claim."""
    body: str                   # e.g. "FSSAI", "EFSA", "PubMed"
    title: str                  # e.g. "FSSAI Regulation 2.3.1"
    url: Optional[str] = None   # Link if available
    year: Optional[int] = None
    detail: Optional[str] = None  # Additional context

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RegulatoryEntry:
    """Regulatory status of an ingredient from a specific body."""
    body: RegulatoryBody
    status: ApprovalStatus
    max_limit: Optional[str] = None     # e.g. "100 ppm", "7.5 mg/kg bw/day"
    limit_context: Optional[str] = None  # e.g. "in beverages", "ADI"
    ins_number: Optional[str] = None     # International Numbering System (E-number)
    source: Optional[Source] = None

    def to_dict(self):
        d = {
            "body": self.body.value,
            "status": self.status.value,
        }
        if self.max_limit:
            d["max_limit"] = self.max_limit
        if self.limit_context:
            d["limit_context"] = self.limit_context
        if self.ins_number:
            d["ins_number"] = self.ins_number
        if self.source:
            d["source"] = self.source.to_dict()
        return d


@dataclass
class IngredientInfo:
    """Complete information about a food ingredient / additive."""
    name: str
    aliases: List[str] = field(default_factory=list)
    e_number: Optional[str] = None          # E102, E621 etc.
    ins_number: Optional[str] = None        # INS number
    category: IngredientCategory = IngredientCategory.OTHER
    description: str = ""
    concern_level: ConcernLevel = ConcernLevel.NONE
    concern_summary: str = ""               # Plain-language summary
    regulatory: List[RegulatoryEntry] = field(default_factory=list)
    sources: List[Source] = field(default_factory=list)
    health_effects: List[str] = field(default_factory=list)
    common_products: List[str] = field(default_factory=list)
    adi: Optional[str] = None               # Acceptable Daily Intake

    def to_dict(self):
        return {
            "name": self.name,
            "aliases": self.aliases,
            "e_number": self.e_number,
            "ins_number": self.ins_number,
            "category": self.category.value,
            "description": self.description,
            "concern_level": self.concern_level.value,
            "concern_summary": self.concern_summary,
            "regulatory": [r.to_dict() for r in self.regulatory],
            "sources": [s.to_dict() for s in self.sources],
            "health_effects": self.health_effects,
            "common_products": self.common_products,
            "adi": self.adi,
        }


# ---------------------------------------------------------------------------
# THE KNOWLEDGE BASE
# ---------------------------------------------------------------------------

# Comprehensive, source-cited ingredient database.
# Every entry traceable to a regulation, published study, or official document.

INGREDIENT_DATABASE: Dict[str, IngredientInfo] = {}


def _register(info: IngredientInfo):
    """Register an ingredient and all its aliases in the database."""
    key = info.name.lower().strip()
    INGREDIENT_DATABASE[key] = info
    for alias in info.aliases:
        INGREDIENT_DATABASE[alias.lower().strip()] = info


# ===== COLORANTS =====

_register(IngredientInfo(
    name="Tartrazine",
    aliases=["e102", "ins 102", "fd&c yellow 5", "yellow 5", "ci 19140", "acid yellow 23"],
    e_number="E102",
    ins_number="102",
    category=IngredientCategory.COLORANT,
    description="Synthetic lemon-yellow azo dye used as a food colorant.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Linked to hyperactivity in children in some studies. Can cause allergic reactions, especially in aspirin-sensitive individuals. Banned in Norway and Austria.",
    adi="0-7.5 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(
            body=RegulatoryBody.FSSAI,
            status=ApprovalStatus.APPROVED_WITH_LIMITS,
            max_limit="100 ppm",
            limit_context="Maximum permitted level in food products",
            ins_number="102",
            source=Source(
                body="FSSAI",
                title="Food Safety and Standards (Food Products Standards and Food Additives) Regulations, 2011 — Appendix A",
                url="https://www.fssai.gov.in/cms/food-safety-and-standards-regulations.php",
                year=2011
            )
        ),
        RegulatoryEntry(
            body=RegulatoryBody.EFSA,
            status=ApprovalStatus.APPROVED_WITH_LIMITS,
            max_limit="7.5 mg/kg bw/day (ADI)",
            limit_context="Acceptable Daily Intake re-evaluated in 2009",
            source=Source(
                body="EFSA",
                title="Scientific Opinion on the re-evaluation of Tartrazine (E 102)",
                url="https://efsa.onlinelibrary.wiley.com/doi/abs/10.2903/j.efsa.2009.1331",
                year=2009
            )
        ),
        RegulatoryEntry(
            body=RegulatoryBody.FDA,
            status=ApprovalStatus.APPROVED,
            source=Source(
                body="FDA",
                title="Color Additive Status List",
                url="https://www.fda.gov/industry/color-additive-inventories/color-additive-status-list",
                year=2024
            )
        ),
    ],
    sources=[
        Source(body="PubMed", title="McCann et al. - Food additives and hyperactive behaviour in 3-year-old and 8/9-year-old children", url="https://pubmed.ncbi.nlm.nih.gov/17825405/", year=2007),
        Source(body="EFSA", title="Re-evaluation of Tartrazine (E 102)", year=2009),
    ],
    health_effects=[
        "May cause hyperactivity in children (Southampton Study, 2007)",
        "Allergic reactions in aspirin-sensitive individuals",
        "Rare cases of urticaria (hives) and asthma",
    ],
    common_products=["soft drinks", "candy", "instant noodles", "pickles", "mustard", "chips"],
))

_register(IngredientInfo(
    name="Sunset Yellow FCF",
    aliases=["e110", "ins 110", "fd&c yellow 6", "yellow 6", "orange yellow s"],
    e_number="E110",
    ins_number="110",
    category=IngredientCategory.COLORANT,
    description="Synthetic orange-red azo dye used as food colorant.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Linked to hyperactivity in children. Can trigger allergic reactions. Banned in Finland and Norway.",
    adi="0-4 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(
            body=RegulatoryBody.FSSAI,
            status=ApprovalStatus.APPROVED_WITH_LIMITS,
            max_limit="100 ppm",
            limit_context="Maximum permitted level in food products",
            source=Source(body="FSSAI", title="Food Additives Regulations, 2011 — Appendix A", year=2011)
        ),
        RegulatoryEntry(
            body=RegulatoryBody.EFSA,
            status=ApprovalStatus.APPROVED_WITH_LIMITS,
            max_limit="4 mg/kg bw/day (ADI)",
            source=Source(body="EFSA", title="Re-evaluation of Sunset Yellow FCF (E 110)", year=2009)
        ),
        RegulatoryEntry(
            body=RegulatoryBody.FDA,
            status=ApprovalStatus.APPROVED,
            source=Source(body="FDA", title="Color Additive Status List", year=2024)
        ),
    ],
    health_effects=[
        "May cause hyperactivity in children",
        "Allergic reactions, especially in aspirin-sensitive individuals",
        "May worsen asthma symptoms",
    ],
    common_products=["orange drinks", "candy", "ice cream", "baked goods"],
))

_register(IngredientInfo(
    name="Brilliant Blue FCF",
    aliases=["e133", "ins 133", "fd&c blue 1", "blue 1", "ci 42090"],
    e_number="E133",
    ins_number="133",
    category=IngredientCategory.COLORANT,
    description="Synthetic blue dye used as a food and beverage colorant.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally considered safe at approved levels. Some reports of allergic reactions.",
    adi="0-12.5 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS, max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Color Additive Status List", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS, max_limit="6 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of Brilliant Blue FCF (E 133)", year=2010)),
    ],
    health_effects=["Rare allergic reactions", "Generally well-tolerated"],
    common_products=["beverages", "candy", "dairy products", "ice cream"],
))

_register(IngredientInfo(
    name="Allura Red AC",
    aliases=["e129", "ins 129", "fd&c red 40", "red 40", "ci 16035"],
    e_number="E129",
    ins_number="129",
    category=IngredientCategory.COLORANT,
    description="Synthetic red azo dye, the most commonly used red food colorant.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Most widely used food dye. Linked to hyperactivity in children in the 2007 Southampton study. Banned in several European countries.",
    adi="0-7 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS, max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Color Additive Status List", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS, max_limit="7 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of Allura Red AC (E 129)", year=2009)),
    ],
    health_effects=[
        "May cause hyperactivity in children",
        "Allergic reactions in some individuals",
        "Some animal studies suggest potential genotoxicity (controversial)",
    ],
    common_products=["soft drinks", "candy", "cereal", "snack foods", "sauces"],
))

_register(IngredientInfo(
    name="Erythrosine",
    aliases=["e127", "ins 127", "fd&c red 3", "red 3", "ci 45430"],
    e_number="E127",
    ins_number="127",
    category=IngredientCategory.COLORANT,
    description="Cherry-red synthetic dye, an iodine-containing colorant.",
    concern_level=ConcernLevel.HIGH,
    concern_summary="Banned in cosmetics by FDA due to thyroid tumor concerns in animal studies. Still permitted in food in limited quantities.",
    adi="0-0.1 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS, max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.RESTRICTED,
                        source=Source(body="FDA", title="Banned in cosmetics; permitted in food with limits", year=1990)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS, max_limit="0.1 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of Erythrosine (E 127)", year=2011)),
    ],
    health_effects=[
        "Thyroid tumors in animal studies at high doses",
        "Affect thyroid hormone levels",
        "Banned in cosmetics by FDA",
        "Very low ADI compared to other dyes",
    ],
    common_products=["candied cherries", "canned fruits", "some medications"],
))


# ===== PRESERVATIVES =====

_register(IngredientInfo(
    name="Sodium Benzoate",
    aliases=["e211", "ins 211", "benzoate of soda"],
    e_number="E211",
    ins_number="211",
    category=IngredientCategory.PRESERVATIVE,
    description="Widely used preservative especially in acidic foods and beverages.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Can form benzene (a carcinogen) when combined with ascorbic acid (vitamin C) in acidic beverages. Linked to hyperactivity in children.",
    adi="0-5 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="600 ppm (in beverages), varies by food category",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        max_limit="0.1% by weight",
                        source=Source(body="FDA", title="21 CFR 184.1733", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="5 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of benzoic acid and sodium benzoate (E 210-213)", year=2016)),
    ],
    health_effects=[
        "Can form benzene when combined with vitamin C in acidic conditions",
        "Linked to hyperactivity in children (Southampton Study)",
        "May cause allergic reactions (urticaria, asthma) in sensitive individuals",
        "Generally safe at approved levels for most people",
    ],
    common_products=["soft drinks", "fruit juices", "pickles", "sauces", "jams"],
))

_register(IngredientInfo(
    name="Sodium Nitrite",
    aliases=["e250", "ins 250", "nitrite"],
    e_number="E250",
    ins_number="250",
    category=IngredientCategory.PRESERVATIVE,
    description="Used to cure meats — gives characteristic pink color and prevents botulism.",
    concern_level=ConcernLevel.HIGH,
    concern_summary="Forms nitrosamines (carcinogenic compounds) when exposed to high heat or combined with amino acids. IARC classifies processed meat (which uses nitrites) as Group 1 carcinogen.",
    adi="0-0.07 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="200 ppm (ingoing amount in meat products)",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="200 ppm in finished product",
                        source=Source(body="FDA", title="21 CFR 172.175", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="0.07 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of sodium nitrite (E 250)", year=2017)),
    ],
    sources=[
        Source(body="IARC", title="IARC Monographs Vol 114 - Red Meat and Processed Meat", url="https://publications.iarc.fr/Book-And-Report-Series/Iarc-Monographs-On-The-Identification-Of-Carcinogenic-Hazards-To-Humans/Red-Meat-And-Processed-Meat-2018", year=2018),
    ],
    health_effects=[
        "Forms carcinogenic nitrosamines at high temperatures",
        "IARC Group 1 carcinogen (in processed meat context)",
        "Essential for preventing botulism in cured meats",
        "May affect oxygen transport in blood (methemoglobinemia) at high doses",
    ],
    common_products=["bacon", "ham", "hot dogs", "sausages", "deli meats", "cured meats"],
))

_register(IngredientInfo(
    name="BHA",
    aliases=["e320", "ins 320", "butylated hydroxyanisole"],
    e_number="E320",
    ins_number="320",
    category=IngredientCategory.ANTIOXIDANT,
    description="Synthetic antioxidant used to prevent fats and oils from going rancid.",
    concern_level=ConcernLevel.HIGH,
    concern_summary="Classified as 'reasonably anticipated to be a human carcinogen' by the US National Toxicology Program. Causes tumors in animal studies.",
    adi="0-0.5 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="200 ppm (in fats and oils)",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        max_limit="0.02% of fat/oil content",
                        source=Source(body="FDA", title="21 CFR 182.3169", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="1 mg/kg bw/day (temporary ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of BHA (E 320)", year=2011)),
    ],
    sources=[
        Source(body="NTP", title="14th Report on Carcinogens - BHA", url="https://ntp.niehs.nih.gov/ntp/roc/content/profiles/butylatedhydroxyanisole.pdf", year=2016),
    ],
    health_effects=[
        "Classified as reasonably anticipated human carcinogen (NTP)",
        "Causes tumors in forestomach of rodents",
        "Endocrine disruption concerns",
        "Allergic reactions in some individuals",
    ],
    common_products=["chips", "butter", "cereal", "instant noodles", "chewing gum"],
))

_register(IngredientInfo(
    name="BHT",
    aliases=["e321", "ins 321", "butylated hydroxytoluene"],
    e_number="E321",
    ins_number="321",
    category=IngredientCategory.ANTIOXIDANT,
    description="Synthetic antioxidant used to preserve fats and oils.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Conflicting evidence on carcinogenicity. Some studies show tumor promotion, others show anti-tumor effects. Banned in some countries.",
    adi="0-0.3 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="200 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        max_limit="0.02% of fat/oil content",
                        source=Source(body="FDA", title="21 CFR 182.3173", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="0.25 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of BHT (E 321)", year=2012)),
    ],
    health_effects=[
        "Conflicting carcinogenicity data (tumor promotion in some studies, anti-tumor in others)",
        "Possible endocrine effects",
        "May cause liver enlargement at high doses",
    ],
    common_products=["cereals", "snack foods", "butter", "dehydrated foods"],
))

_register(IngredientInfo(
    name="TBHQ",
    aliases=["e319", "ins 319", "tert-butylhydroquinone", "tertiary butylhydroquinone"],
    e_number="E319",
    ins_number="319",
    category=IngredientCategory.ANTIOXIDANT,
    description="Synthetic antioxidant derived from butane, used in oils and processed foods.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="At high doses, causes stomach tumors in animal studies. May affect immune system. Can cause nausea, vomiting at very high intake.",
    adi="0-0.7 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="200 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        max_limit="0.02% of fat/oil content",
                        source=Source(body="FDA", title="21 CFR 172.185", year=2024)),
    ],
    health_effects=[
        "Stomach tumors in animal studies at high doses",
        "May impair immune response",
        "Nausea and vomiting at very high intake (5g+)",
    ],
    common_products=["cooking oils", "instant noodles", "frozen foods", "crackers", "microwave popcorn"],
))

_register(IngredientInfo(
    name="Potassium Sorbate",
    aliases=["e202", "ins 202", "sorbic acid potassium salt"],
    e_number="E202",
    ins_number="202",
    category=IngredientCategory.PRESERVATIVE,
    description="Widely used preservative effective against molds and yeasts.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally considered one of the safest preservatives. Rare allergic reactions. Very low toxicity profile.",
    adi="0-25 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.3640", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="25 mg/kg bw/day (group ADI for sorbic acid and sorbates)",
                        source=Source(body="EFSA", title="Re-evaluation of sorbic acid and potassium sorbate", year=2015)),
    ],
    health_effects=["Generally safe", "Rare skin sensitization", "Very low toxicity"],
    common_products=["cheese", "wine", "baked goods", "dried fruits", "personal care products"],
))


# ===== SWEETENERS =====

_register(IngredientInfo(
    name="Aspartame",
    aliases=["e951", "ins 951", "nutrasweet", "equal", "canderel"],
    e_number="E951",
    ins_number="951",
    category=IngredientCategory.SWEETENER,
    description="Low-calorie artificial sweetener, about 200 times sweeter than sugar.",
    concern_level=ConcernLevel.CONTROVERSIAL,
    concern_summary="WHO/IARC classified as 'possibly carcinogenic' (Group 2B) in 2023, but JECFA maintained existing ADI saying evidence is not convincing. Extensively studied — over 100 studies reviewed.",
    adi="0-40 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="Varies by food category (e.g. 700 ppm in beverages)",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        max_limit="50 mg/kg bw/day (ADI)",
                        source=Source(body="FDA", title="Aspartame approval", year=1981)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="40 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Scientific Opinion on the re-evaluation of aspartame (E 951)", year=2013)),
        RegulatoryEntry(body=RegulatoryBody.WHO, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="40 mg/kg bw/day (ADI maintained by JECFA)",
                        source=Source(body="WHO/IARC", title="IARC Monographs Vol 134 — Aspartame classified Group 2B", url="https://www.iarc.who.int/news-events/aspartame-hazard-and-risk-assessment-results-released/", year=2023)),
    ],
    sources=[
        Source(body="WHO", title="WHO/IARC Aspartame hazard and risk assessment", year=2023, url="https://www.who.int/news/item/14-07-2023-aspartame-hazard-and-risk-assessment-results-released"),
    ],
    health_effects=[
        "IARC Group 2B: possibly carcinogenic to humans (2023)",
        "JECFA: existing ADI of 40 mg/kg bw/day remains unchanged",
        "Unsafe for people with phenylketonuria (PKU) — contains phenylalanine",
        "Headaches and migraines reported by some consumers",
        "Over 100 safety studies reviewed — no consensus on harm at normal intake",
    ],
    common_products=["diet sodas", "sugar-free gum", "tabletop sweeteners", "sugar-free desserts", "protein shakes"],
))

_register(IngredientInfo(
    name="Sucralose",
    aliases=["e955", "ins 955", "splenda"],
    e_number="E955",
    ins_number="955",
    category=IngredientCategory.SWEETENER,
    description="Artificial sweetener about 600 times sweeter than sugar. Made from sugar but not metabolized.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally considered safe by major regulators. Recent studies raise questions about gut microbiome effects and DNA damage at very high doses, but evidence is limited.",
    adi="0-15 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        max_limit="5 mg/kg bw/day (ADI)",
                        source=Source(body="FDA", title="Sucralose approval", year=1998)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="15 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Scientific Opinion on sucralose (E 955)", year=2016)),
    ],
    health_effects=[
        "Possible effects on gut microbiome composition",
        "A 2023 study suggested genotoxicity of sucralose-6-acetate (metabolite) — not yet confirmed",
        "Generally well-tolerated at normal consumption levels",
    ],
    common_products=["diet beverages", "sugar-free products", "baked goods", "protein bars"],
))

_register(IngredientInfo(
    name="Acesulfame Potassium",
    aliases=["e950", "ins 950", "acesulfame k", "ace-k", "sunett", "sweet one"],
    e_number="E950",
    ins_number="950",
    category=IngredientCategory.SWEETENER,
    description="Artificial sweetener about 200 times sweeter than sugar, often blended with other sweeteners.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Approved by all major regulators. Some older studies questioned its carcinogenicity, but these were found to have methodological issues. EFSA confirmed safety in 2020.",
    adi="0-15 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        max_limit="15 mg/kg bw/day (ADI)",
                        source=Source(body="FDA", title="Acesulfame K approval", year=1988)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="9 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of Acesulfame K (E 950)", year=2020)),
    ],
    health_effects=["Generally safe at approved levels", "Bitter aftertaste at high concentrations"],
    common_products=["diet sodas", "sugar-free gum", "dairy products", "baked goods"],
))

_register(IngredientInfo(
    name="Stevia",
    aliases=["e960", "ins 960", "steviol glycosides", "stevia rebaudiana", "reb a", "rebaudioside a", "truvia"],
    e_number="E960",
    ins_number="960",
    category=IngredientCategory.SWEETENER,
    description="Natural sweetener extracted from the leaves of Stevia rebaudiana plant. 200-300 times sweeter than sugar.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural origin. Approved by all major regulators. No significant safety concerns at approved levels. Used for centuries in South America.",
    adi="0-4 mg/kg body weight/day (expressed as steviol)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS Notice for high-purity steviol glycosides", year=2008)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="4 mg/kg bw/day (as steviol)",
                        source=Source(body="EFSA", title="Scientific Opinion on steviol glycosides (E 960)", year=2010)),
    ],
    health_effects=["No significant safety concerns", "May have blood pressure-lowering effects", "Natural origin"],
    common_products=["beverages", "tabletop sweeteners", "dairy products", "baked goods"],
))


# ===== FLAVOR ENHANCERS =====

_register(IngredientInfo(
    name="Monosodium Glutamate",
    aliases=["e621", "ins 621", "msg", "ajinomoto", "umami seasoning", "glutamic acid"],
    e_number="E621",
    ins_number="621",
    category=IngredientCategory.FLAVOR_ENHANCER,
    description="Flavor enhancer that provides umami taste. Sodium salt of glutamic acid.",
    concern_level=ConcernLevel.CONTROVERSIAL,
    concern_summary="'Chinese Restaurant Syndrome' claims largely debunked by science. FDA classified GRAS. However, some individuals report sensitivity symptoms. Naturally occurs in tomatoes, cheese, mushrooms.",
    adi="Not specified (JECFA considers it safe at normal food usage levels)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="10 g/kg of food (1%)",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="Questions and Answers on MSG", url="https://www.fda.gov/food/food-additives-petitions/questions-and-answers-monosodium-glutamate-msg", year=2012)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="30 mg/kg bw/day (group ADI for glutamic acid and glutamates)",
                        source=Source(body="EFSA", title="Re-evaluation of glutamic acid and glutamates (E 620-625)", year=2017)),
    ],
    sources=[
        Source(body="PubMed", title="Monosodium glutamate is not associated with obesity or a greater prevalence of weight gain over 5 years", url="https://pubmed.ncbi.nlm.nih.gov/21372742/", year=2011),
    ],
    health_effects=[
        "'Chinese Restaurant Syndrome' largely debunked — no consistent scientific evidence",
        "Some individuals may experience headache, flushing, sweating (MSG sensitivity)",
        "Occurs naturally in tomatoes, parmesan cheese, mushrooms, seaweed",
        "EFSA set group ADI of 30 mg/kg bw/day in 2017",
    ],
    common_products=["chips", "instant noodles", "soups", "snack foods", "fast food", "Chinese food"],
))


# ===== EMULSIFIERS & THICKENERS =====

_register(IngredientInfo(
    name="Carrageenan",
    aliases=["e407", "ins 407", "irish moss extract"],
    e_number="E407",
    ins_number="407",
    category=IngredientCategory.THICKENER,
    description="Natural thickener and stabilizer extracted from red seaweed.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Food-grade carrageenan is generally safe, but degraded carrageenan (poligeenan) is a known carcinogen. Concerns about intestinal inflammation in animal studies.",
    adi="Not specified (JECFA considers acceptable for food use)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="21 CFR 172.620", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="75 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of carrageenan (E 407)", year=2018)),
    ],
    health_effects=[
        "Food-grade carrageenan generally safe",
        "Degraded carrageenan (poligeenan) is carcinogenic — but not used in food",
        "May cause intestinal inflammation in animal studies",
        "Some evidence of gut microbiome disruption",
    ],
    common_products=["ice cream", "milk alternatives", "processed meats", "yogurt", "infant formula"],
))

_register(IngredientInfo(
    name="Xanthan Gum",
    aliases=["e415", "ins 415"],
    e_number="E415",
    ins_number="415",
    category=IngredientCategory.THICKENER,
    description="Polysaccharide produced by bacterial fermentation, used as a thickener and stabilizer.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Generally considered very safe. Used widely in gluten-free products. Can cause digestive issues (bloating, gas) at very high intake.",
    adi="Not specified (considered safe at current usage levels)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="21 CFR 172.695", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="Safety of xanthan gum (E 415)", year=2017)),
    ],
    health_effects=["Gas and bloating at high intake", "Laxative effect at very high doses", "Generally safe"],
    common_products=["salad dressings", "sauces", "gluten-free products", "ice cream", "bakery products"],
))

_register(IngredientInfo(
    name="Guar Gum",
    aliases=["e412", "ins 412", "guar flour", "guaran"],
    e_number="E412",
    ins_number="412",
    category=IngredientCategory.THICKENER,
    description="Natural thickener from guar beans, commonly used in Indian food industry.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Very safe. India is the world's largest producer. May cause digestive discomfort at high doses. Used in ayurvedic medicine.",
    adi="Not specified (considered safe)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1339", year=2024)),
    ],
    health_effects=["May cause bloating at high intake", "Lowers cholesterol", "Slows sugar absorption"],
    common_products=["ice cream", "sauces", "bakery products", "dairy products"],
))


# ===== SUGARS & HIDDEN SUGARS =====

_register(IngredientInfo(
    name="High Fructose Corn Syrup",
    aliases=["hfcs", "glucose-fructose syrup", "isoglucose", "corn sugar", "hfcs-55", "hfcs-42"],
    category=IngredientCategory.SUGAR,
    description="Sweetener made from corn starch, where some glucose is converted to fructose.",
    concern_level=ConcernLevel.HIGH,
    concern_summary="Strongly linked to obesity epidemic, type 2 diabetes, non-alcoholic fatty liver disease and metabolic syndrome. Metabolized differently than regular sugar — primarily by the liver.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted as a sweetener in food products", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS status for HFCS", year=1983)),
    ],
    sources=[
        Source(body="PubMed", title="Consumption of HFCS and risk of metabolic syndrome and type 2 diabetes", url="https://pubmed.ncbi.nlm.nih.gov/20516261/", year=2010),
    ],
    health_effects=[
        "Contributes to obesity and weight gain",
        "Increases risk of type 2 diabetes",
        "Non-alcoholic fatty liver disease (NAFLD)",
        "Metabolic syndrome",
        "Increased uric acid production → gout risk",
        "Metabolized primarily by the liver (unlike glucose)",
    ],
    common_products=["sodas", "juices", "candy", "cereals", "bread", "condiments", "yogurt"],
))

_register(IngredientInfo(
    name="Maltodextrin",
    aliases=["maltodextrine"],
    category=IngredientCategory.SUGAR,
    description="Highly processed starch-derived food additive. Has a very high glycemic index (85-105, higher than table sugar).",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Very high glycemic index — spikes blood sugar rapidly. Often used in 'sugar-free' products as a bulking agent while still affecting blood sugar. May alter gut bacteria.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted as a food additive", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS status", year=2024)),
    ],
    health_effects=[
        "Glycemic index of 85-105 (higher than table sugar at 65)",
        "Spikes blood sugar rapidly — problematic for diabetics",
        "May suppress growth of beneficial gut bacteria",
        "Can promote growth of E. coli and other pathogens",
        "Often hidden in 'sugar-free' products",
    ],
    common_products=["protein powders", "sugar-free products", "instant foods", "snacks", "sauces"],
))


# ===== TRANS FATS / HYDROGENATED OILS =====

_register(IngredientInfo(
    name="Partially Hydrogenated Oil",
    aliases=["partially hydrogenated vegetable oil", "partially hydrogenated soybean oil",
             "partially hydrogenated palm oil", "vanaspati", "dalda"],
    category=IngredientCategory.FAT_OIL,
    description="Oil processed to become solid at room temperature. Primary dietary source of artificial trans fats.",
    concern_level=ConcernLevel.HIGH,
    concern_summary="WHO called for worldwide elimination by 2023. FSSAI capped trans fat at 2% (2022). Strongly linked to heart disease, stroke, and type 2 diabetes. Banned by FDA in 2018.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.RESTRICTED,
                        max_limit="2% trans fat in oils and fats (from Jan 2022)",
                        source=Source(body="FSSAI", title="Food Safety and Standards (Prohibition and Restrictions on Sales) Amendment Regulations, 2021",
                                      url="https://www.fssai.gov.in/upload/notifications/2021/08/6116eb8b12bf5Gazette_Notification_TFA_03_08_2021.pdf", year=2021)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.BANNED,
                        source=Source(body="FDA", title="Final Determination Regarding Partially Hydrogenated Oils — no longer GRAS",
                                      url="https://www.federalregister.gov/documents/2015/06/17/2015-14883", year=2018)),
        RegulatoryEntry(body=RegulatoryBody.WHO, status=ApprovalStatus.BANNED,
                        source=Source(body="WHO", title="REPLACE trans fat — WHO plan to eliminate industrially-produced trans-fatty acids",
                                      url="https://www.who.int/teams/nutrition-and-food-safety/replace-trans-fat", year=2018)),
    ],
    sources=[
        Source(body="WHO", title="REPLACE action package to eliminate industrially-produced trans fats", year=2018),
        Source(body="FSSAI", title="India caps trans fat at 2% — among most aggressive limits globally", year=2022),
    ],
    health_effects=[
        "Increases LDL (bad) cholesterol, decreases HDL (good) cholesterol",
        "Strongly linked to coronary heart disease",
        "Increases risk of stroke",
        "Contributes to type 2 diabetes",
        "Promotes inflammation",
        "FDA banned as 'not generally recognized as safe' (2018)",
        "WHO called for global elimination by 2023",
    ],
    common_products=["margarine", "vanaspati/dalda", "baked goods", "fried foods", "crackers", "cookies"],
))


# ===== REFINED INGREDIENTS =====

_register(IngredientInfo(
    name="Maida",
    aliases=["refined wheat flour", "all-purpose flour", "all purpose flour", "white flour",
             "bleached flour", "enriched flour", "refined flour"],
    category=IngredientCategory.GRAIN_FLOUR,
    description="Highly refined wheat flour stripped of bran and germ. Staple in Indian processed foods.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Stripped of fiber, vitamins, and minerals during processing. High glycemic index. Bleaching agents may be used. Not inherently toxic but offers poor nutrition.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted in food products — Standards for wheat flour", year=2011)),
    ],
    sources=[
        Source(body="IFCT 2017", title="Indian Food Composition Tables — Comparison of whole wheat vs refined flour", year=2017),
    ],
    health_effects=[
        "High glycemic index — spikes blood sugar",
        "Stripped of fiber (whole wheat: 12.5g fiber; maida: 0.3g per 100g)",
        "May use chemical bleaching agents (benzoyl peroxide)",
        "Contributes to constipation due to lack of fiber",
        "Not inherently toxic — but nutritionally poor",
    ],
    common_products=["bread", "biscuits", "naan", "samosa", "cakes", "pasta", "noodles"],
))


# ---------------------------------------------------------------------------
# LOOKUP FUNCTIONS
# ---------------------------------------------------------------------------

def lookup_ingredient(name: str) -> Optional[IngredientInfo]:
    """
    Look up an ingredient by name or alias.
    Returns IngredientInfo if found, None otherwise.
    """
    key = name.lower().strip()
    if key in INGREDIENT_DATABASE:
        return INGREDIENT_DATABASE[key]

    # Fuzzy-ish matching: check if query is substring of any key
    for db_key, info in INGREDIENT_DATABASE.items():
        if key in db_key or db_key in key:
            return info

    return None


def lookup_ingredients_batch(names: List[str]) -> Dict[str, Optional[IngredientInfo]]:
    """Look up multiple ingredients at once."""
    return {name: lookup_ingredient(name) for name in names}


def get_all_ingredient_names() -> List[str]:
    """Get all unique ingredient names (not aliases)."""
    seen = set()
    names = []
    for info in INGREDIENT_DATABASE.values():
        if info.name not in seen:
            seen.add(info.name)
            names.append(info.name)
    return sorted(names)


def search_ingredients(query: str) -> List[IngredientInfo]:
    """Search ingredients by partial name match."""
    query_lower = query.lower().strip()
    results = []
    seen = set()
    for key, info in INGREDIENT_DATABASE.items():
        if query_lower in key and info.name not in seen:
            results.append(info)
            seen.add(info.name)
    return results


def get_ingredients_by_concern(level: ConcernLevel) -> List[IngredientInfo]:
    """Get all ingredients at a specific concern level."""
    seen = set()
    results = []
    for info in INGREDIENT_DATABASE.values():
        if info.concern_level == level and info.name not in seen:
            results.append(info)
            seen.add(info.name)
    return results


def get_ingredients_by_category(cat: IngredientCategory) -> List[IngredientInfo]:
    """Get all ingredients of a specific category."""
    seen = set()
    results = []
    for info in INGREDIENT_DATABASE.values():
        if info.category == cat and info.name not in seen:
            results.append(info)
            seen.add(info.name)
    return results


# ---------------------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------------------

def get_database_stats() -> Dict[str, Any]:
    """Get statistics about the knowledge base."""
    unique = {}
    for info in INGREDIENT_DATABASE.values():
        unique[info.name] = info

    by_category = {}
    by_concern = {}
    for info in unique.values():
        by_category[info.category.value] = by_category.get(info.category.value, 0) + 1
        by_concern[info.concern_level.value] = by_concern.get(info.concern_level.value, 0) + 1

    return {
        "total_ingredients": len(unique),
        "total_aliases": len(INGREDIENT_DATABASE),
        "by_category": by_category,
        "by_concern_level": by_concern,
    }
