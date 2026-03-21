"""
LLM Explainer — Generates rich, source-cited ingredient explanations.

Uses Ollama (free, local, open-source) with Llama 3.1 8B by default.
Falls back to template-based explanations if Ollama is unavailable.

Architecture:
  1. Receives ingredient name + KB data + RAG context
  2. Builds a structured prompt enforcing source citations
  3. Sends to Ollama via HTTP API (localhost:11434)
  4. Returns plain-language explanation with sources

No API keys needed. No cloud dependency. Fully private.
"""
import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "90"))  # seconds (first call loads model)

# System prompt that enforces our "decode, don't judge" philosophy
SYSTEM_PROMPT = """You are an ingredient intelligence assistant for EatSmartly, an Indian food label decoder app.

RULES — follow these strictly:
1. NEVER say food is "safe" or "unsafe" — you are not a doctor
2. ALWAYS cite sources: say "According to FSSAI..." or "EFSA states..." or "Per the FSSAI Compendium (p.XX)..."
3. Keep it simple — explain like talking to a curious 15-year-old
4. Be factual and neutral — present what regulators say, not personal opinions
5. If the source mentions a limit, state it: "Permitted up to X ppm in beverages"
6. Mention if something is banned in any country — that's a fact, not a judgment
7. Keep response to 2-4 sentences for each ingredient
8. For Indian context: always mention FSSAI status first, then international regulators
9. End with the source in brackets like [FSSAI Compendium p.47] or [EFSA 2021]"""


# ---------------------------------------------------------------------------
# Ollama Client
# ---------------------------------------------------------------------------

class OllamaClient:
    """Lightweight async client for Ollama HTTP API."""

    def __init__(self, base_url: str = None, model: str = None, timeout: int = None):
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.model = model or OLLAMA_MODEL
        self.timeout = timeout or OLLAMA_TIMEOUT
        self._available = None  # Cached availability check

    async def is_available(self) -> bool:
        """Check if Ollama server is running."""
        if self._available is not None:
            return self._available

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                self._available = resp.status_code == 200
                if self._available:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    logger.info(f"Ollama available. Models: {models}")
                    if not any(self.model.split(":")[0] in m for m in models):
                        logger.warning(
                            f"Model '{self.model}' not found in Ollama. "
                            f"Available: {models}. Run: ollama pull {self.model}"
                        )
                return self._available
        except Exception as e:
            logger.info(f"Ollama not available at {self.base_url}: {e}")
            self._available = False
            return False

    async def generate(self, prompt: str, system: str = None) -> Optional[str]:
        """Generate a completion from Ollama."""
        if not await self.is_available():
            return None

        try:
            import httpx
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system or SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Low temp for factual responses
                    "top_p": 0.9,
                    "num_predict": 300,  # Keep responses concise
                },
            }

            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=10)) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "").strip()
                else:
                    logger.warning(f"Ollama returned {resp.status_code}: {resp.text[:200]}")
                    return None
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            return None

    def reset_availability(self):
        """Reset cached availability (call if Ollama was just started)."""
        self._available = None


# Singleton
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

def _build_ingredient_prompt(
    ingredient_name: str,
    kb_data: Optional[Dict[str, Any]] = None,
    rag_context: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Build a structured prompt for the LLM using KB data + RAG passages.

    The prompt includes all available facts so the LLM just needs to
    synthesize — not invent — information.
    """
    parts = [f"Explain this food ingredient to an Indian consumer: **{ingredient_name}**\n"]

    # Add structured KB data if available
    if kb_data:
        parts.append("=== DATA FROM OUR REGULATORY DATABASE ===")
        if kb_data.get("category"):
            parts.append(f"Category: {kb_data['category']}")
        if kb_data.get("e_number"):
            parts.append(f"E/INS Number: {kb_data['e_number']}")
        if kb_data.get("concern_level"):
            parts.append(f"Concern Level: {kb_data['concern_level']}")
        if kb_data.get("concern_summary"):
            parts.append(f"Summary: {kb_data['concern_summary']}")
        if kb_data.get("adi"):
            parts.append(f"ADI: {kb_data['adi']}")

        # Regulatory status
        for reg in kb_data.get("regulatory_status", []):
            status_str = f"{reg.get('body', '')}: {reg.get('status', '')}"
            if reg.get("max_limit"):
                status_str += f" (limit: {reg['max_limit']})"
            parts.append(status_str)

        # Health effects
        effects = kb_data.get("health_effects", [])
        if effects:
            parts.append(f"Health effects: {'; '.join(effects)}")

        # Sources
        for src in kb_data.get("sources", []):
            parts.append(f"Source: {src.get('title', '')} ({src.get('year', '')})")

    # Add RAG passages from FSSAI/IFCT PDFs
    if rag_context:
        parts.append("\n=== PASSAGES FROM REGULATORY DOCUMENTS ===")
        for i, ctx in enumerate(rag_context[:3], 1):
            source = ctx.get("source", "Unknown")
            page = ctx.get("page", "?")
            text = ctx.get("text", "")[:400]
            parts.append(f"[Passage {i}] {source} (p.{page}): {text}")

    parts.append(
        "\n=== INSTRUCTIONS ==="
        "\nUsing ONLY the data and passages above, write a 2-4 sentence explanation."
        "\nCite your sources in brackets. Do NOT invent information not in the data."
        "\nStart directly with the explanation — no preamble."
    )

    return "\n".join(parts)


def _build_product_prompt(
    product_name: str,
    decoded_ingredients: List[Dict[str, Any]],
) -> str:
    """Build a prompt for summarizing a full product's ingredient profile."""
    parts = [
        f"Summarize the ingredient profile of **{product_name}** for an Indian consumer.\n",
        "=== DECODED INGREDIENTS ===",
    ]

    for ing in decoded_ingredients:
        concern = ing.get("concern_level", "unknown")
        category = ing.get("category", "unknown")
        name = ing.get("name", "unknown")
        parts.append(f"  {ing.get('position', '?')}. {name} ({category}) — concern: {concern}")

    warnings = [i for i in decoded_ingredients if i.get("concern_level") in ("high", "moderate", "controversial")]
    if warnings:
        parts.append(f"\nIngredients of concern: {', '.join(w['name'] for w in warnings)}")

    parts.append(
        "\n=== INSTRUCTIONS ==="
        "\nWrite a 3-5 sentence summary."
        "\nHighlight any ingredients of concern and why."
        "\nMention the transparency score if most ingredients are identified."
        "\nDo NOT say the product is safe or unsafe."
        "\nStart directly — no preamble."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def explain_ingredient(
    ingredient_name: str,
    kb_data: Optional[Dict[str, Any]] = None,
    rag_context: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generate a rich, AI-powered explanation for an ingredient.

    Args:
        ingredient_name: Name of the ingredient
        kb_data: Data from our regulatory knowledge base (if available)
        rag_context: RAG-retrieved passages from FSSAI/IFCT PDFs

    Returns:
        Dict with 'explanation', 'model', 'source' keys
    """
    client = get_ollama_client()

    prompt = _build_ingredient_prompt(ingredient_name, kb_data, rag_context)
    response = await client.generate(prompt)

    if response:
        return {
            "explanation": response,
            "model": client.model,
            "source": "ollama",
            "generated": True,
        }
    else:
        # Fallback: return a structured explanation from KB data without LLM
        fallback = _template_explanation(ingredient_name, kb_data, rag_context)
        return {
            "explanation": fallback,
            "model": "template",
            "source": "fallback",
            "generated": False,
        }


async def explain_product(
    product_name: str,
    decoded_ingredients: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate an AI-powered summary of a product's ingredient profile.
    """
    client = get_ollama_client()

    prompt = _build_product_prompt(product_name, decoded_ingredients)
    response = await client.generate(prompt)

    if response:
        return {
            "summary": response,
            "model": client.model,
            "source": "ollama",
            "generated": True,
        }
    else:
        return {
            "summary": _template_product_summary(product_name, decoded_ingredients),
            "model": "template",
            "source": "fallback",
            "generated": False,
        }


def _template_explanation(
    name: str,
    kb_data: Optional[Dict] = None,
    rag_context: Optional[List[Dict]] = None,
) -> str:
    """Template fallback when Ollama is unavailable."""
    if kb_data:
        parts = []
        cat = kb_data.get("category", "food ingredient")
        parts.append(f"{name} is a {cat}.")
        if kb_data.get("concern_summary"):
            parts.append(kb_data["concern_summary"])
        for reg in kb_data.get("regulatory_status", [])[:2]:
            if reg.get("max_limit"):
                parts.append(f"{reg['body']} permits with limit: {reg['max_limit']}.")
        return " ".join(parts)
    elif rag_context:
        best = rag_context[0]
        return (
            f"{name} — found in {best.get('source', 'regulatory documents')} "
            f"(p.{best.get('page', '?')}). {best.get('text', '')[:200]}..."
        )
    else:
        return f"{name} — no detailed information available yet."


def _template_product_summary(
    product_name: str,
    decoded_ingredients: List[Dict],
) -> str:
    """Template fallback for product summary."""
    total = len(decoded_ingredients)
    known = sum(1 for i in decoded_ingredients if i.get("known"))
    concerns = [i["name"] for i in decoded_ingredients if i.get("concern_level") in ("high", "moderate")]

    parts = [f"{product_name} contains {total} ingredients, {known} identified in our database."]
    if concerns:
        parts.append(f"Ingredients of note: {', '.join(concerns)}.")
    else:
        parts.append("No ingredients of significant concern found.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Sync wrappers (for use in non-async contexts)
# ---------------------------------------------------------------------------

def explain_ingredient_sync(
    ingredient_name: str,
    kb_data: Optional[Dict] = None,
    rag_context: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Sync wrapper for explain_ingredient."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context — can't use run_until_complete
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    explain_ingredient(ingredient_name, kb_data, rag_context)
                )
                return future.result(timeout=OLLAMA_TIMEOUT + 5)
        else:
            return loop.run_until_complete(
                explain_ingredient(ingredient_name, kb_data, rag_context)
            )
    except Exception as e:
        logger.warning(f"Sync explain_ingredient failed: {e}")
        return {
            "explanation": _template_explanation(ingredient_name, kb_data, rag_context),
            "model": "template",
            "source": "fallback",
            "generated": False,
        }
