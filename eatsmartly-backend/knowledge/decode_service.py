"""
Ingredient Decode Service — The core intelligence layer.

Takes raw ingredient text → parses it → looks up each ingredient in the
regulatory knowledge base → returns source-cited, plain-language explanations.

This is the service that powers the "We don't judge food. We decode labels." approach.
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from knowledge.regulatory_db import (
    lookup_ingredient,
    IngredientInfo,
    ConcernLevel,
    IngredientCategory,
    get_database_stats,
)
from knowledge.ingredient_parser import (
    parse_ingredient_list,
    ParsedIngredient,
    extract_ingredient_names,
    detect_ingredient_list,
)
from agents.utils import setup_logger
from config import settings

logger = setup_logger(__name__, settings.LOG_LEVEL)

# ---------------------------------------------------------------------------
# RAG fallback — lazy-loaded singleton
# ---------------------------------------------------------------------------
_rag_pipeline = None


def _get_rag_pipeline():
    """Lazy-load RAG pipeline only when needed (and only if indexed)."""
    global _rag_pipeline
    if _rag_pipeline is not None:
        return _rag_pipeline
    try:
        from knowledge.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline()
        if pipeline.is_ready:
            _rag_pipeline = pipeline
            logger.info(f"RAG pipeline loaded — {pipeline.store.size} chunks available")
            return _rag_pipeline
        else:
            logger.info("RAG pipeline not yet indexed — fallback disabled")
            return None
    except Exception as e:
        logger.warning(f"Could not load RAG pipeline: {e}")
        return None


# ---------------------------------------------------------------------------
# Data classes for decode results
# ---------------------------------------------------------------------------

@dataclass
class IngredientDecodeResult:
    """Result of decoding a single ingredient."""
    name: str
    position: int                    # Position in list (1 = most by weight)
    category: Optional[str] = None
    known: bool = False              # Whether we found it in the knowledge base
    concern_level: Optional[str] = None
    concern_summary: Optional[str] = None
    regulatory_status: List[Dict] = field(default_factory=list)
    health_effects: List[str] = field(default_factory=list)
    sources: List[Dict] = field(default_factory=list)
    adi: Optional[str] = None
    e_number: Optional[str] = None
    plain_explanation: str = ""      # Simple, human-readable explanation
    sub_ingredients: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "position": self.position,
            "known": self.known,
            "plain_explanation": self.plain_explanation,
        }
        if self.category:
            d["category"] = self.category
        if self.concern_level:
            d["concern_level"] = self.concern_level
        if self.concern_summary:
            d["concern_summary"] = self.concern_summary
        if self.regulatory_status:
            d["regulatory_status"] = self.regulatory_status
        if self.health_effects:
            d["health_effects"] = self.health_effects
        if self.sources:
            d["sources"] = self.sources
        if self.adi:
            d["adi"] = self.adi
        if self.e_number:
            d["e_number"] = self.e_number
        if self.sub_ingredients:
            d["sub_ingredients"] = self.sub_ingredients
        return d


@dataclass
class LabelDecodeResult:
    """Full result of decoding a product's ingredient label."""
    product_name: Optional[str] = None
    total_ingredients: int = 0
    ingredients_identified: int = 0
    ingredients_unknown: int = 0
    overall_concern: str = "none"     # Highest concern level found
    decoded_ingredients: List[IngredientDecodeResult] = field(default_factory=list)
    summary: str = ""
    warnings: List[Dict[str, str]] = field(default_factory=list)
    transparency_score: float = 0.0   # % of ingredients we could identify
    sources_cited: int = 0
    disclaimer: str = (
        "This information is aggregated from public regulatory databases "
        "(FSSAI, FDA, EFSA, CODEX, PubMed). EatSmartly does not make health claims. "
        "Consult a healthcare professional for dietary advice."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_name": self.product_name,
            "total_ingredients": self.total_ingredients,
            "ingredients_identified": self.ingredients_identified,
            "ingredients_unknown": self.ingredients_unknown,
            "overall_concern": self.overall_concern,
            "transparency_score": round(self.transparency_score, 1),
            "sources_cited": self.sources_cited,
            "summary": self.summary,
            "warnings": self.warnings,
            "decoded_ingredients": [i.to_dict() for i in self.decoded_ingredients],
            "disclaimer": self.disclaimer,
        }


# ---------------------------------------------------------------------------
# Concern level ordering for comparison
# ---------------------------------------------------------------------------

CONCERN_ORDER = {
    ConcernLevel.NONE: 0,
    ConcernLevel.LOW: 1,
    ConcernLevel.MODERATE: 2,
    ConcernLevel.CONTROVERSIAL: 3,
    ConcernLevel.HIGH: 4,
}


# ---------------------------------------------------------------------------
# Plain-language explanation generator
# ---------------------------------------------------------------------------

def _generate_plain_explanation(info: IngredientInfo) -> str:
    """Generate a simple, human-readable explanation for an ingredient."""
    parts = []

    # What is it?
    cat_labels = {
        IngredientCategory.PRESERVATIVE: "a preservative",
        IngredientCategory.COLORANT: "a food colorant/dye",
        IngredientCategory.SWEETENER: "a sweetener",
        IngredientCategory.EMULSIFIER: "an emulsifier",
        IngredientCategory.STABILIZER: "a stabilizer",
        IngredientCategory.THICKENER: "a thickener",
        IngredientCategory.FLAVOR_ENHANCER: "a flavor enhancer",
        IngredientCategory.ANTIOXIDANT: "an antioxidant/preservative",
        IngredientCategory.ACIDITY_REGULATOR: "an acidity regulator",
        IngredientCategory.SUGAR: "a sugar/sweetener",
        IngredientCategory.FAT_OIL: "a fat/oil",
        IngredientCategory.GRAIN_FLOUR: "a grain/flour product",
    }
    cat_desc = cat_labels.get(info.category, "a food ingredient")
    parts.append(f"{info.name} is {cat_desc}.")

    # Concern level
    concern_msgs = {
        ConcernLevel.NONE: "No significant safety concerns at normal consumption levels.",
        ConcernLevel.LOW: "Generally considered safe with minor concerns noted in some studies.",
        ConcernLevel.MODERATE: "Some health concerns raised in scientific literature.",
        ConcernLevel.HIGH: "Significant health concerns documented in scientific literature.",
        ConcernLevel.CONTROVERSIAL: "Actively debated in scientific community — conflicting evidence exists.",
    }
    if info.concern_level in concern_msgs:
        parts.append(concern_msgs[info.concern_level])

    # Key regulatory info
    for reg in info.regulatory[:2]:  # Top 2 regulatory entries
        if reg.max_limit:
            parts.append(f"{reg.body.value} permits with limit: {reg.max_limit}.")
        elif reg.status.value == "banned":
            parts.append(f"Banned by {reg.body.value}.")
        elif reg.status.value == "gras":
            parts.append(f"Classified as Generally Recognized As Safe by {reg.body.value}.")

    return " ".join(parts)


def _generate_unknown_explanation(name: str, position: int) -> str:
    """Generate explanation for an ingredient not in our database."""
    if position <= 3:
        return (
            f"{name} — not yet in our regulatory database. "
            f"Listed at position {position} (one of the main ingredients by weight)."
        )
    return f"{name} — not yet in our regulatory database."


def _rag_fallback_for_ingredient(name: str, position: int) -> IngredientDecodeResult:
    """
    Use RAG pipeline to find relevant info from FSSAI/IFCT PDFs for
    an ingredient not in our manual database.
    """
    pipeline = _get_rag_pipeline()
    if not pipeline:
        return IngredientDecodeResult(
            name=name,
            position=position,
            known=False,
            plain_explanation=_generate_unknown_explanation(name, position),
        )

    try:
        rag_result = pipeline.explain_ingredient(name, top_k=3)
    except Exception as e:
        logger.warning(f"RAG retrieval failed for '{name}': {e}")
        return IngredientDecodeResult(
            name=name,
            position=position,
            known=False,
            plain_explanation=_generate_unknown_explanation(name, position),
        )

    if not rag_result.get("found"):
        return IngredientDecodeResult(
            name=name,
            position=position,
            known=False,
            plain_explanation=_generate_unknown_explanation(name, position),
        )

    # Build explanation from RAG context
    contexts = rag_result.get("context", [])
    best = contexts[0] if contexts else None

    # Only use if relevance is above threshold
    if not best or best.get("relevance", 0) < 0.25:
        return IngredientDecodeResult(
            name=name,
            position=position,
            known=False,
            plain_explanation=_generate_unknown_explanation(name, position),
        )

    # Build a sourced explanation from retrieved document passages
    rag_sources = []
    rag_snippets = []
    for ctx in contexts:
        if ctx.get("relevance", 0) >= 0.20:
            snippet = ctx["text"][:300].strip()
            src_label = ctx.get("source", "Regulatory Document")
            page = ctx.get("page")
            rag_snippets.append(snippet)
            src_dict = {"body": src_label, "title": src_label}
            if page:
                src_dict["detail"] = f"Page {page}"
            rag_sources.append(src_dict)

    explanation = (
        f"{name} — not in our curated database, but found references in regulatory documents. "
        + rag_snippets[0][:200] + "..."
    ) if rag_snippets else _generate_unknown_explanation(name, position)

    return IngredientDecodeResult(
        name=name,
        position=position,
        known=False,
        concern_level="unknown",
        plain_explanation=explanation,
        sources=rag_sources,
    )


# ---------------------------------------------------------------------------
# Core decode function
# ---------------------------------------------------------------------------

def decode_ingredients(
    ingredient_text: str,
    product_name: Optional[str] = None,
    raw_ocr_text: Optional[str] = None,
) -> LabelDecodeResult:
    """
    Decode a product's ingredient list into source-cited information.

    Args:
        ingredient_text: Ingredient list text (can be messy/OCR)
        product_name: Optional product name for context
        raw_ocr_text: Full OCR text (if ingredients need to be auto-detected)

    Returns:
        LabelDecodeResult with decoded, sourced information
    """
    # If no ingredient text but raw OCR provided, try to auto-detect
    if not ingredient_text and raw_ocr_text:
        ingredient_text = detect_ingredient_list(raw_ocr_text) or ""

    if not ingredient_text:
        return LabelDecodeResult(
            product_name=product_name,
            summary="No ingredient information available for this product.",
        )

    # Parse the ingredient list
    parsed = parse_ingredient_list(ingredient_text)

    if not parsed:
        return LabelDecodeResult(
            product_name=product_name,
            summary="Could not parse ingredient list from the provided text.",
        )

    # Decode each ingredient
    decoded = []
    identified = 0
    unknown = 0
    highest_concern = ConcernLevel.NONE
    total_sources = 0
    warnings = []

    for p in parsed:
        info = lookup_ingredient(p.normalized_name)

        if info:
            identified += 1

            # Track highest concern
            if CONCERN_ORDER.get(info.concern_level, 0) > CONCERN_ORDER.get(highest_concern, 0):
                highest_concern = info.concern_level

            total_sources += len(info.sources) + len(info.regulatory)

            result = IngredientDecodeResult(
                name=info.name,
                position=p.position,
                category=info.category.value,
                known=True,
                concern_level=info.concern_level.value,
                concern_summary=info.concern_summary,
                regulatory_status=[r.to_dict() for r in info.regulatory],
                health_effects=info.health_effects,
                sources=[s.to_dict() for s in info.sources],
                adi=info.adi,
                e_number=info.e_number,
                plain_explanation=_generate_plain_explanation(info),
                sub_ingredients=p.sub_ingredients,
            )

            # Generate warnings for high/moderate concern ingredients
            if info.concern_level in (ConcernLevel.HIGH, ConcernLevel.CONTROVERSIAL):
                warnings.append({
                    "ingredient": info.name,
                    "level": info.concern_level.value,
                    "message": info.concern_summary,
                    "position": p.position,
                })
            elif info.concern_level == ConcernLevel.MODERATE and p.position <= 5:
                warnings.append({
                    "ingredient": info.name,
                    "level": "moderate",
                    "message": info.concern_summary,
                    "position": p.position,
                })
        else:
            unknown += 1
            # RAG fallback: search FSSAI/IFCT PDFs for context
            result = _rag_fallback_for_ingredient(p.normalized_name, p.position)
            result.sub_ingredients = p.sub_ingredients
            # If RAG found sources, count them
            if result.sources:
                total_sources += len(result.sources)

        decoded.append(result)

    # Sort warnings by position (earlier = more by weight)
    warnings.sort(key=lambda w: w["position"])

    # Calculate transparency score
    total = len(parsed)
    transparency = (identified / total * 100) if total > 0 else 0

    # Generate summary
    summary = _generate_summary(
        product_name=product_name,
        total=total,
        identified=identified,
        unknown=unknown,
        highest_concern=highest_concern,
        warnings=warnings,
    )

    return LabelDecodeResult(
        product_name=product_name,
        total_ingredients=total,
        ingredients_identified=identified,
        ingredients_unknown=unknown,
        overall_concern=highest_concern.value,
        decoded_ingredients=decoded,
        summary=summary,
        warnings=warnings,
        transparency_score=transparency,
        sources_cited=total_sources,
    )


def _generate_summary(
    product_name: Optional[str],
    total: int,
    identified: int,
    unknown: int,
    highest_concern: ConcernLevel,
    warnings: List[Dict],
) -> str:
    """Generate a human-readable summary of the decode results."""
    parts = []

    name = product_name or "This product"
    parts.append(f"{name} contains {total} ingredient(s).")
    parts.append(f"We identified {identified} in our regulatory database ({unknown} unknown).")

    if not warnings:
        parts.append("No ingredients of significant concern were found based on current regulatory data.")
    else:
        concern_names = [w["ingredient"] for w in warnings]
        if len(concern_names) <= 3:
            parts.append(f"Ingredients of note: {', '.join(concern_names)}.")
        else:
            parts.append(f"{len(concern_names)} ingredients flagged for review — see details below.")

    concern_msgs = {
        ConcernLevel.NONE: "",
        ConcernLevel.LOW: "",
        ConcernLevel.MODERATE: "Some ingredients have moderate concerns in scientific literature.",
        ConcernLevel.HIGH: "This product contains ingredients with significant concerns documented in peer-reviewed research.",
        ConcernLevel.CONTROVERSIAL: "This product contains ingredients with actively debated safety profiles.",
    }
    msg = concern_msgs.get(highest_concern, "")
    if msg:
        parts.append(msg)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Quick-decode helper (for API)
# ---------------------------------------------------------------------------

def quick_decode(ingredient_text: str, product_name: str = "") -> Dict[str, Any]:
    """
    Quick decode for API use. Returns a dict ready for JSON serialization.
    """
    result = decode_ingredients(ingredient_text, product_name)
    return result.to_dict()


# ---------------------------------------------------------------------------
# Compare two products
# ---------------------------------------------------------------------------

def compare_products(
    product_a_ingredients: str,
    product_b_ingredients: str,
    product_a_name: str = "Product A",
    product_b_name: str = "Product B",
) -> Dict[str, Any]:
    """
    Compare two products' ingredient profiles side by side.
    """
    decode_a = decode_ingredients(product_a_ingredients, product_a_name)
    decode_b = decode_ingredients(product_b_ingredients, product_b_name)

    # Find common concerning ingredients
    concerns_a = {w["ingredient"] for w in decode_a.warnings}
    concerns_b = {w["ingredient"] for w in decode_b.warnings}
    common_concerns = concerns_a & concerns_b
    only_a = concerns_a - concerns_b
    only_b = concerns_b - concerns_a

    # Determine which is "simpler" (fewer total ingredients, more identified)
    simpler = None
    if decode_a.total_ingredients < decode_b.total_ingredients:
        simpler = product_a_name
    elif decode_b.total_ingredients < decode_a.total_ingredients:
        simpler = product_b_name

    comparison_summary = []
    if common_concerns:
        comparison_summary.append(f"Both contain: {', '.join(common_concerns)}")
    if only_a:
        comparison_summary.append(f"Only in {product_a_name}: {', '.join(only_a)}")
    if only_b:
        comparison_summary.append(f"Only in {product_b_name}: {', '.join(only_b)}")
    if simpler:
        comparison_summary.append(f"{simpler} has a simpler ingredient list.")

    return {
        "product_a": decode_a.to_dict(),
        "product_b": decode_b.to_dict(),
        "comparison": {
            "common_concerns": list(common_concerns),
            "only_in_a": list(only_a),
            "only_in_b": list(only_b),
            "simpler_product": simpler,
            "summary": " ".join(comparison_summary) if comparison_summary else "Both products have similar profiles.",
        },
        "disclaimer": decode_a.disclaimer,
    }
