"""
Ingredient Parser — NLP-based extraction and normalization of ingredients from food labels.

Parses messy OCR text or ingredient lists into structured, normalized ingredient entries
that can be looked up against the regulatory knowledge base.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ParsedIngredient:
    """A single ingredient extracted from an ingredient list."""
    raw_text: str                          # Original text as-is
    normalized_name: str                   # Cleaned, normalized name
    quantity: Optional[str] = None         # e.g. "0.5%", "100mg"
    qualifier: Optional[str] = None        # e.g. "contains permitted", "as stabilizer"
    sub_ingredients: List[str] = field(default_factory=list)  # Nested ingredients
    position: int = 0                      # Position in list (1 = first = most by weight)
    confidence: float = 1.0               # Parsing confidence

    def to_dict(self):
        d = {
            "raw_text": self.raw_text,
            "normalized_name": self.normalized_name,
            "position": self.position,
        }
        if self.quantity:
            d["quantity"] = self.quantity
        if self.qualifier:
            d["qualifier"] = self.qualifier
        if self.sub_ingredients:
            d["sub_ingredients"] = self.sub_ingredients
        if self.confidence < 1.0:
            d["confidence"] = round(self.confidence, 2)
        return d


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Common OCR errors and misspellings
OCR_CORRECTIONS = {
    "sodlum": "sodium",
    "suqar": "sugar",
    "artifical": "artificial",
    "flavour": "flavor",
    "colour": "color",
    "coiour": "color",
    "colouring": "coloring",
    "flavouring": "flavoring",
    "sulphur": "sulfur",
    "sulphate": "sulfate",
    "carbohyrate": "carbohydrate",
    "protel n": "protein",
    "proteln": "protein",
    "hydrogeneted": "hydrogenated",
    "benzoete": "benzoate",
    "aspartarne": "aspartame",
    "saccharin e": "saccharine",
    "pottasium": "potassium",
    "potasium": "potassium",
    "sorbote": "sorbate",
    "carboxymethyl cellulose": "carboxymethylcellulose",
    "e.d.t.a": "edta",
    "mono and di glycerides": "mono and diglycerides",
    "m.s.g": "msg",
    "m.s.g.": "msg",
    "b.h.a": "bha",
    "b.h.t": "bht",
    "t.b.h.q": "tbhq",
    "b.h.a.": "bha",
    "b.h.t.": "bht",
    "t.b.h.q.": "tbhq",
    "h.f.c.s": "hfcs",
    "colour(s)": "color",
    "emulsifier(s)": "emulsifier",
    "stabiliser(s)": "stabilizer",
    "stabiliser": "stabilizer",
    "thickner": "thickener",
}

# Pattern: INS/E-number references like "INS 102", "(E102)", "INS102"
INS_PATTERN = re.compile(
    r'\b(?:ins|e)\s*[-]?\s*(\d{3,4}[a-z]?(?:\s*\([iv]+\))?)\b',
    re.IGNORECASE
)

# Quantity patterns like "0.5%", "100mg/kg", "≤200ppm"
QUANTITY_PATTERN = re.compile(
    r'[\(\[]?\s*(?:≤|<=|<|>|≥|>=|~|approx\.?)?\s*'
    r'(\d+(?:\.\d+)?)\s*'
    r'(%|ppm|mg(?:/kg)?|g(?:/kg)?|ml|mcg|µg|iu)\s*'
    r'[\)\]]?',
    re.IGNORECASE
)

# Qualifier patterns
QUALIFIER_PATTERN = re.compile(
    r'\b(contains permitted|as (?:a )?(?:stabilizer|emulsifier|preservative|anti[- ]?oxidant|thickener|color(?:ing)?|acidity regulator)s?'
    r'|used as|added as|acts as|for (?:color|flavor|preservation))\b',
    re.IGNORECASE
)

# Noise words to strip from ingredient names
NOISE_WORDS = {
    "contains", "permitted", "class", "ii", "synthetic", "food",
    "grade", "added", "used", "for", "purpose", "of", "type",
}


# ---------------------------------------------------------------------------
# Core Parsing
# ---------------------------------------------------------------------------

def parse_ingredient_list(text: str) -> List[ParsedIngredient]:
    """
    Parse a raw ingredient list string into structured ParsedIngredient objects.

    Handles:
    - Comma-separated and period-separated lists
    - Nested parentheses: "Sugar (contains: glucose, fructose)"
    - INS/E-number annotations: "Tartrazine (INS 102)"
    - Quantities: "Salt (0.5%)"
    - OCR artefacts and common misspellings
    - Indian-style "Ingredients:" prefix
    """
    if not text or not text.strip():
        return []

    # Step 1: Pre-clean
    cleaned = _pre_clean(text)

    # Step 2: Split into raw parts
    raw_parts = _split_ingredients(cleaned)

    # Step 3: Parse each part
    ingredients = []
    for i, raw in enumerate(raw_parts, 1):
        parsed = _parse_single(raw, position=i)
        if parsed:
            ingredients.append(parsed)

    return ingredients


def _pre_clean(text: str) -> str:
    """Pre-process the raw text before splitting."""
    # Remove "Ingredients:" prefix (common on labels)
    text = re.sub(r'^(?:ingredients?\s*[:;.\-–—]?\s*)', '', text, flags=re.IGNORECASE)

    # Normalise whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Replace common OCR artefacts
    text = text.replace('|', 'l')  # pipe → l
    text = text.replace('0', 'O') if text.count('0') > text.count('o') + 5 else text

    # Apply known OCR corrections
    text_lower = text.lower()
    for wrong, right in OCR_CORRECTIONS.items():
        text_lower = text_lower.replace(wrong, right)

    # Normalise separator variants
    text_lower = text_lower.replace(';', ',')

    return text_lower


def _split_ingredients(text: str) -> List[str]:
    """
    Split ingredient text into individual items.
    Respects parenthesis nesting.
    """
    parts = []
    current = []
    depth = 0

    for char in text:
        if char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth = max(0, depth - 1)
            current.append(char)
        elif char == ',' and depth == 0:
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(char)

    # Last segment
    part = ''.join(current).strip()
    if part:
        parts.append(part)

    # If we got only 1 part (no commas), try splitting on period
    if len(parts) == 1 and '.' in parts[0]:
        dot_parts = [p.strip() for p in parts[0].split('.') if p.strip()]
        if len(dot_parts) > 1:
            parts = dot_parts

    return parts


def _parse_single(raw: str, position: int) -> Optional[ParsedIngredient]:
    """Parse a single ingredient string."""
    text = raw.strip().strip('.,;:-–—')
    if not text or len(text) < 2:
        return None

    # Skip if it's just a number or boilerplate
    if re.match(r'^\d+$', text):
        return None
    if any(skip in text for skip in ['best before', 'mfg', 'batch no', 'net wt', 'mrp']):
        return None

    # Extract quantity if present
    quantity = None
    qty_match = QUANTITY_PATTERN.search(text)
    if qty_match:
        quantity = qty_match.group(0).strip('()[] ')
        text = QUANTITY_PATTERN.sub('', text).strip()

    # Extract qualifier if present
    qualifier = None
    qual_match = QUALIFIER_PATTERN.search(text)
    if qual_match:
        qualifier = qual_match.group(0).strip()

    # Extract sub-ingredients from parentheses
    sub_ingredients = []
    paren_match = re.search(r'\(([^()]+)\)', text)
    if paren_match:
        inner = paren_match.group(1)
        # Check if it's sub-ingredients (contains commas or "and")
        if ',' in inner or ' and ' in inner:
            sub_parts = re.split(r',\s*|\s+and\s+', inner)
            sub_ingredients = [s.strip() for s in sub_parts if s.strip() and len(s.strip()) > 1]

    # Extract INS/E numbers
    ins_match = INS_PATTERN.search(text)
    ins_number = ins_match.group(1) if ins_match else None

    # Clean the name: remove parenthetical content, INS numbers, qualifiers
    name = text
    name = re.sub(r'\([^)]*\)', '', name)           # Remove parentheticals
    name = INS_PATTERN.sub('', name)                  # Remove INS/E refs
    name = QUANTITY_PATTERN.sub('', name)              # Remove quantities
    if qualifier:
        name = name.replace(qualifier, '')
    name = re.sub(r'\s+', ' ', name).strip().strip('.,;:-–— ')

    # If we found an INS number but no clean name, use the INS as the name
    if (not name or len(name) < 2) and ins_number:
        name = f"ins {ins_number}"

    if not name or len(name) < 2:
        return None

    return ParsedIngredient(
        raw_text=raw.strip(),
        normalized_name=name,
        quantity=quantity,
        qualifier=qualifier,
        sub_ingredients=sub_ingredients,
        position=position,
        confidence=_estimate_confidence(name, raw),
    )


def _estimate_confidence(normalized: str, raw: str) -> float:
    """Estimate parsing confidence (0-1)."""
    conf = 1.0

    # Very short names are suspect
    if len(normalized) < 3:
        conf -= 0.3

    # All numbers → probably not an ingredient name
    if re.match(r'^[\d\s.,%]+$', normalized):
        conf -= 0.5

    # Contains unusual characters
    if re.search(r'[#@$^&*{}|\\<>]', normalized):
        conf -= 0.2

    return max(0.1, conf)


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------

def extract_ingredient_names(text: str) -> List[str]:
    """Quick helper: just get normalized names from an ingredient list."""
    return [p.normalized_name for p in parse_ingredient_list(text)]


def extract_ins_numbers(text: str) -> List[str]:
    """Extract all INS/E numbers from text."""
    return [m.group(1) for m in INS_PATTERN.finditer(text.lower())]


def detect_ingredient_list(text: str) -> Optional[str]:
    """
    Given a full OCR text dump, try to find and extract just the ingredients section.
    """
    # Look for "Ingredients:" header
    patterns = [
        r'ingredients?\s*[:;.\-–—]\s*(.+?)(?=\n\s*(?:nutrition|allergen|storage|best before|mfg|batch|net w|contains|may contain)|\Z)',
        r'(?:composition|contents?)\s*[:;.\-–—]\s*(.+?)(?=\n\s*(?:nutrition|allergen|storage)|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    return None
