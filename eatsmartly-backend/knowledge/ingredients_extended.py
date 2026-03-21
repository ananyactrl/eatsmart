"""
Extended Ingredient Database — Batch 2.

Common additives found on Indian packaged food labels (Maggi, Britannia, Parle,
Amul, Haldirams, ITC, etc.) plus globally common additives.

Auto-registered into the main INGREDIENT_DATABASE on import.
"""
from knowledge.regulatory_db import (
    _register, IngredientInfo, IngredientCategory, ConcernLevel,
    RegulatoryEntry, RegulatoryBody, ApprovalStatus, Source,
)


# =====================================================================
# EMULSIFIERS (very common on Indian labels)
# =====================================================================

_register(IngredientInfo(
    name="Soy Lecithin",
    aliases=["e322", "ins 322", "lecithin", "soya lecithin", "soy lecithin (e322)"],
    e_number="E322",
    ins_number="322",
    category=IngredientCategory.EMULSIFIER,
    description="Natural emulsifier derived from soybeans. One of the most common food additives.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Generally considered very safe. Allergen risk for soy-allergic individuals. Found in nearly all chocolate, baked goods, and processed foods.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1400", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="Lecithins (E 322) — ADI not specified", year=2017)),
    ],
    health_effects=["Allergen: contains soy proteins", "Generally very safe", "May support brain health (choline source)"],
    common_products=["chocolate", "biscuits", "bread", "margarine", "instant noodles", "ice cream"],
))

_register(IngredientInfo(
    name="Mono- and Diglycerides of Fatty Acids",
    aliases=["e471", "ins 471", "mono and diglycerides", "glyceryl monostearate", "gms",
             "monoglycerides", "diglycerides"],
    e_number="E471",
    ins_number="471",
    category=IngredientCategory.EMULSIFIER,
    description="Emulsifiers made from glycerol and fatty acids. Used to improve texture in bread, ice cream, and margarine.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Considered safe by all major regulators. Made from fats naturally present in food. No ADI specified.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1505", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="No safety concern at current usage levels", year=2017)),
    ],
    health_effects=["Metabolized like normal dietary fats", "No safety concerns at approved levels"],
    common_products=["bread", "ice cream", "margarine", "cakes", "biscuits"],
))

_register(IngredientInfo(
    name="Polysorbate 80",
    aliases=["e433", "ins 433", "tween 80", "polyoxyethylene sorbitan monooleate"],
    e_number="E433",
    ins_number="433",
    category=IngredientCategory.EMULSIFIER,
    description="Synthetic emulsifier used in ice cream, sauces, and pharmaceuticals.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Some animal studies suggest it may promote intestinal inflammation and alter gut microbiome. Used extensively in vaccines and medications as well.",
    adi="0-25 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        max_limit="Up to 1% in most foods",
                        source=Source(body="FDA", title="21 CFR 172.840", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="25 mg/kg bw/day (group ADI for polysorbates)",
                        source=Source(body="EFSA", title="Re-evaluation of polysorbates (E 432-436)", year=2015)),
    ],
    sources=[
        Source(body="PubMed", title="Chassaing et al. - Dietary emulsifiers impact the mouse gut microbiota promoting colitis and metabolic syndrome", url="https://pubmed.ncbi.nlm.nih.gov/25731162/", year=2015),
    ],
    health_effects=[
        "May promote intestinal inflammation in animal studies",
        "Possible gut microbiome alteration",
        "Generally safe at approved levels in humans",
    ],
    common_products=["ice cream", "sauces", "pickles", "pharmaceutical products"],
))

_register(IngredientInfo(
    name="Sodium Stearoyl Lactylate",
    aliases=["e481", "ins 481", "ssl", "sodium stearoyl-2-lactylate"],
    e_number="E481",
    ins_number="481",
    category=IngredientCategory.EMULSIFIER,
    description="Emulsifier and dough strengthener commonly used in bread and baked goods.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Considered safe. Metabolized to stearic acid and lactic acid, both naturally occurring in the body.",
    adi="0-22 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 172.846", year=2024)),
    ],
    health_effects=["Metabolized to naturally occurring compounds", "No significant safety concerns"],
    common_products=["bread", "biscuits", "cakes", "pancake mixes"],
))

_register(IngredientInfo(
    name="DATEM",
    aliases=["e472e", "ins 472e", "diacetyl tartaric acid esters of mono- and diglycerides",
             "diacetyl tartaric acid ester"],
    e_number="E472e",
    ins_number="472e",
    category=IngredientCategory.EMULSIFIER,
    description="Dough conditioner and emulsifier used in bread to improve volume and texture.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Generally safe. Widely used in commercial bread. Metabolized to tartaric acid, glycerol, and fatty acids.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1101", year=2024)),
    ],
    health_effects=["No significant safety concerns", "Metabolized to natural compounds"],
    common_products=["bread", "rolls", "buns", "tortillas"],
))


# =====================================================================
# ACIDITY REGULATORS (very common INS numbers on Indian labels)
# =====================================================================

_register(IngredientInfo(
    name="Citric Acid",
    aliases=["e330", "ins 330", "citric acid anhydrous", "2-hydroxypropane-1,2,3-tricarboxylic acid"],
    e_number="E330",
    ins_number="330",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Naturally occurring acid found in citrus fruits. Most widely used food acid in the world.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Naturally found in lemons, oranges, and all citrus. Extremely safe. Produced industrially by fermentation. No ADI specified.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.1033", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="No safety concern — quantum satis", year=2016)),
    ],
    health_effects=["Naturally occurring in citrus fruits", "Very safe", "May erode tooth enamel at very high concentrations"],
    common_products=["soft drinks", "candy", "jams", "sauces", "canned foods", "beverages"],
))

_register(IngredientInfo(
    name="Phosphoric Acid",
    aliases=["e338", "ins 338", "orthophosphoric acid"],
    e_number="E338",
    ins_number="338",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Mineral acid used primarily in cola beverages for sharp, tangy taste.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="High intakes associated with lower bone mineral density and kidney issues. Cola beverages are the main dietary source.",
    adi="70 mg/kg body weight/day (as phosphorus, group MTDI)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.1073", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="40 mg/kg bw/day (revised ADI as phosphorus)",
                        source=Source(body="EFSA", title="Re-evaluation of phosphoric acid and phosphates (E 338-341, E 343, E 450-452)", year=2019)),
    ],
    sources=[
        Source(body="PubMed", title="Tucker et al. - Cola, but not other carbonated beverages, are associated with low bone mineral density", url="https://pubmed.ncbi.nlm.nih.gov/17023723/", year=2006),
    ],
    health_effects=[
        "Cola consumption linked to lower bone mineral density",
        "Excess phosphorus may affect calcium absorption",
        "May contribute to kidney stone formation at high intake",
        "Tooth enamel erosion",
    ],
    common_products=["cola drinks (Coca-Cola, Pepsi, Thums Up)", "processed cheese", "flavored water"],
))

_register(IngredientInfo(
    name="Sodium Bicarbonate",
    aliases=["e500", "ins 500", "ins 500ii", "baking soda", "sodium hydrogen carbonate"],
    e_number="E500",
    ins_number="500",
    category=IngredientCategory.RAISING_AGENT,
    description="Common baking soda, used as a leavening agent in baked goods.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Very safe household ingredient. Used in cooking for centuries. Also used as an antacid.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1736", year=2024)),
    ],
    health_effects=["Very safe at normal usage", "Used as antacid medicine", "Excessive use may cause alkalosis"],
    common_products=["biscuits", "cakes", "bread", "instant noodles", "cookies"],
))

_register(IngredientInfo(
    name="Ammonium Bicarbonate",
    aliases=["e503", "ins 503", "ins 503ii", "ammonium hydrogen carbonate"],
    e_number="E503",
    ins_number="503",
    category=IngredientCategory.RAISING_AGENT,
    description="Leavening agent used in flat baked goods like crackers and biscuits.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Safe. Decomposes completely into carbon dioxide, water, and ammonia during baking. Leaves no residue.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1135", year=2024)),
    ],
    health_effects=["Completely decomposes during baking", "No residue in finished product", "Very safe"],
    common_products=["crackers", "biscuits", "cookies", "flat baked goods"],
))

_register(IngredientInfo(
    name="Calcium Carbonate",
    aliases=["e170", "ins 170", "chalk", "limestone", "calcite"],
    e_number="E170",
    ins_number="170",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Natural mineral used as acidity regulator, anti-caking agent, and calcium supplement.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Very safe. Used as a calcium supplement. Found naturally in chalk, limestone, and seashells.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1191", year=2024)),
    ],
    health_effects=["Used as calcium supplement", "Very safe", "Antacid properties"],
    common_products=["fortified foods", "bread", "cereals", "supplements", "toothpaste"],
))

_register(IngredientInfo(
    name="Sodium Citrate",
    aliases=["e331", "ins 331", "trisodium citrate", "sodium citrate dihydrate"],
    e_number="E331",
    ins_number="331",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Sodium salt of citric acid. Used as acidity regulator and emulsifier.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Very safe. Used in beverages, gelatin products, and as blood anticoagulant in medical use.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.1751", year=2024)),
    ],
    health_effects=["Very safe", "Used in medicine as blood anticoagulant"],
    common_products=["soft drinks", "energy drinks", "gelatin desserts", "processed cheese"],
))

_register(IngredientInfo(
    name="Lactic Acid",
    aliases=["e270", "ins 270", "milk acid"],
    e_number="E270",
    ins_number="270",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Naturally occurring acid produced during fermentation. Found in yogurt, sauerkraut, and sourdough.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Naturally produced in the body during exercise. Found in all fermented foods. Extremely safe.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1061", year=2024)),
    ],
    health_effects=["Naturally produced in the body", "Found in all fermented foods", "Very safe"],
    common_products=["yogurt", "pickles", "sauerkraut", "sourdough bread", "beer", "olives"],
))

_register(IngredientInfo(
    name="Tartaric Acid",
    aliases=["e334", "ins 334", "l-tartaric acid", "dihydroxybutanedioic acid"],
    e_number="E334",
    ins_number="334",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Naturally occurring acid found in grapes and wine. Used in baking powder.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Naturally found in grapes, bananas, and tamarind. Safe. Used in cream of tartar for baking.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1099", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="30 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of tartaric acid and tartrates", year=2020)),
    ],
    health_effects=["Naturally found in grapes and tamarind", "Very safe at food-use levels"],
    common_products=["baking powder", "wine", "candy", "soft drinks"],
))

_register(IngredientInfo(
    name="Malic Acid",
    aliases=["e296", "ins 296", "dl-malic acid", "apple acid"],
    e_number="E296",
    ins_number="296",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="Naturally occurring acid found in apples and many fruits. Gives sour taste.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Naturally occurs in apples, grapes, and most fruits. Produced in the body during metabolism (Krebs cycle). Extremely safe.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1069", year=2024)),
    ],
    health_effects=["Natural component of the Krebs cycle in human metabolism", "Found in all apples", "Tooth enamel erosion at high concentrations"],
    common_products=["sour candy", "fruit-flavored beverages", "wine", "cider"],
))

_register(IngredientInfo(
    name="Acetic Acid",
    aliases=["e260", "ins 260", "vinegar", "ethanoic acid", "glacial acetic acid"],
    e_number="E260",
    ins_number="260",
    category=IngredientCategory.ACIDITY_REGULATOR,
    description="The acid in vinegar. Used as preservative and flavoring agent.",
    concern_level=ConcernLevel.NONE,
    concern_summary="The main component of vinegar, used for thousands of years. Extremely safe in food use.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1005", year=2024)),
    ],
    health_effects=["Main component of vinegar", "Used for thousands of years", "Very safe"],
    common_products=["vinegar", "pickles", "sauces", "ketchup", "mayonnaise", "chutneys"],
))


# =====================================================================
# MORE PRESERVATIVES
# =====================================================================

_register(IngredientInfo(
    name="Calcium Propionate",
    aliases=["e282", "ins 282", "calcium propanoate"],
    e_number="E282",
    ins_number="282",
    category=IngredientCategory.PRESERVATIVE,
    description="Preservative that inhibits mold growth. Most widely used bread preservative.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally safe. One Australian study linked it to irritability and restlessness in children, but not widely replicated.",
    adi="Not specified (JECFA considers acceptable at current food use levels)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="3000 ppm in bread",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1221", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="Re-evaluation of propionic acid and propionates", year=2014)),
    ],
    health_effects=[
        "One study linked to irritability in children (not widely replicated)",
        "May cause migraine in sensitive individuals",
        "Generally safe at approved levels",
    ],
    common_products=["bread", "tortillas", "baked goods", "processed cheese"],
))

_register(IngredientInfo(
    name="Sorbic Acid",
    aliases=["e200", "ins 200"],
    e_number="E200",
    ins_number="200",
    category=IngredientCategory.PRESERVATIVE,
    description="Naturally occurring preservative found in berries of the mountain ash tree.",
    concern_level=ConcernLevel.NONE,
    concern_summary="One of the safest preservatives. Natural origin (mountain ash berries). Very low toxicity.",
    adi="0-25 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.3089", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="25 mg/kg bw/day (group ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of sorbic acid", year=2015)),
    ],
    health_effects=["Natural origin", "Very low toxicity", "Rare skin sensitization"],
    common_products=["cheese", "wine", "baked goods", "dried fruits"],
))

_register(IngredientInfo(
    name="Sulfur Dioxide",
    aliases=["e220", "ins 220", "sulphur dioxide", "so2", "sulphites", "sulfites"],
    e_number="E220",
    ins_number="220",
    category=IngredientCategory.PRESERVATIVE,
    description="Preservative and antioxidant used in dried fruits, wine, and processed foods.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Can trigger severe asthma attacks in sulfite-sensitive individuals (estimated 5-10% of asthmatics). Must be declared on labels if >10 ppm.",
    adi="0-0.7 mg/kg body weight/day (as SO2)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="Varies: 50-2000 ppm depending on food category",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FDA", title="Banned on raw fruits/vegetables; permitted in processed foods", year=1986)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="0.7 mg/kg bw/day (group ADI as SO2)",
                        source=Source(body="EFSA", title="Re-evaluation of sulfites (E 220-228)", year=2016)),
    ],
    health_effects=[
        "Severe asthma attacks in sulfite-sensitive individuals",
        "Headaches and migraines in sensitive people",
        "Must be declared as allergen on labels",
        "Destroys vitamin B1 (thiamine) in food",
    ],
    common_products=["dried fruits", "wine", "beer", "fruit juices", "pickled foods", "jam"],
))

_register(IngredientInfo(
    name="Sodium Metabisulfite",
    aliases=["e223", "ins 223", "sodium metabisulphite", "sodium pyrosulfite", "disodium disulfite"],
    e_number="E223",
    ins_number="223",
    category=IngredientCategory.PRESERVATIVE,
    description="Sulfite preservative and antioxidant. Common in Indian food processing.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Same risks as sulfur dioxide — dangerous for asthmatics sensitive to sulfites. Widely used in Indian food industry.",
    adi="0-0.7 mg/kg body weight/day (as SO2, group ADI)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.3766", year=2024)),
    ],
    health_effects=[
        "Triggers severe asthma in sulfite-sensitive individuals",
        "Allergen — must be declared",
        "Destroys vitamin B1",
    ],
    common_products=["dried fruits", "pickles", "fruit juices", "wine", "instant noodles seasoning"],
))

_register(IngredientInfo(
    name="Nisin",
    aliases=["e234", "ins 234", "nisin preparation"],
    e_number="E234",
    ins_number="234",
    category=IngredientCategory.PRESERVATIVE,
    description="Natural antimicrobial peptide produced by Lactococcus lactis bacteria. Used in cheese and canned foods.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural origin — produced by bacteria found in milk. Used in Indian paneer and cheese preservation. Very safe.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="12.5 mg/kg in cheese and paneer",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS Notice GRN 65", year=2001)),
    ],
    health_effects=["Natural antimicrobial from milk bacteria", "Very safe", "Degrades in digestive system"],
    common_products=["cheese", "paneer", "canned vegetables", "processed cheese spread"],
))


# =====================================================================
# MORE COLORANTS (common on Indian labels)
# =====================================================================

_register(IngredientInfo(
    name="Carmoisine",
    aliases=["e122", "ins 122", "azorubine", "food red 3", "acid red 14"],
    e_number="E122",
    ins_number="122",
    category=IngredientCategory.COLORANT,
    description="Synthetic red azo dye used in food, especially in Indian sweets and beverages.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Linked to hyperactivity in children (Southampton Study 2007). Banned in USA, Sweden, and Norway. Still widely used in India.",
    adi="0-4 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.BANNED,
                        source=Source(body="FDA", title="Not approved for use in the United States", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="4 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of Carmoisine (E 122)", year=2009)),
    ],
    sources=[
        Source(body="PubMed", title="McCann et al. - Food additives and hyperactive behaviour in children", url="https://pubmed.ncbi.nlm.nih.gov/17825405/", year=2007),
    ],
    health_effects=[
        "Linked to hyperactivity in children",
        "Banned in USA and several countries",
        "May cause allergic reactions in aspirin-sensitive individuals",
    ],
    common_products=["Indian sweets", "beverages", "jams", "candy", "ice cream"],
))

_register(IngredientInfo(
    name="Ponceau 4R",
    aliases=["e124", "ins 124", "cochineal red a", "brilliant scarlet", "new coccine"],
    e_number="E124",
    ins_number="124",
    category=IngredientCategory.COLORANT,
    description="Synthetic red azo dye. Very commonly used in Indian food products.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Included in Southampton Study linking food dyes to hyperactivity. Banned in USA and Norway. Very commonly used in India.",
    adi="0-4 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.BANNED,
                        source=Source(body="FDA", title="Not approved for use in the United States", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="4 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Re-evaluation of Ponceau 4R (E 124)", year=2009)),
    ],
    health_effects=[
        "Linked to hyperactivity in children",
        "Banned in USA",
        "May trigger asthma and urticaria in sensitive individuals",
    ],
    common_products=["Indian sweets", "beverages", "sausages", "cake mixes", "jelly"],
))

_register(IngredientInfo(
    name="Quinoline Yellow",
    aliases=["e104", "ins 104", "quinoline yellow ws", "food yellow 13"],
    e_number="E104",
    ins_number="104",
    category=IngredientCategory.COLORANT,
    description="Synthetic yellow-green dye used in food and cosmetics.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="Linked to hyperactivity. Banned in USA, Australia, Japan, and Norway. Still permitted in India and EU with limits.",
    adi="0-3 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.BANNED,
                        source=Source(body="FDA", title="Not approved for use in the United States", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="0.5 mg/kg bw/day (ADI, reduced from 10 in 2009)",
                        source=Source(body="EFSA", title="Re-evaluation of Quinoline Yellow (E 104)", year=2009)),
    ],
    health_effects=[
        "Linked to hyperactivity in children",
        "Banned in USA, Australia, Japan, Norway",
        "EFSA significantly reduced ADI in 2009",
    ],
    common_products=["ice cream", "scotch eggs", "smoked fish", "candy"],
))

_register(IngredientInfo(
    name="Caramel Color",
    aliases=["e150", "ins 150", "e150a", "e150b", "e150c", "e150d", "ins 150a", "ins 150d",
             "caramel colour", "caramel coloring", "class iv caramel", "ammonia caramel"],
    e_number="E150",
    ins_number="150",
    category=IngredientCategory.COLORANT,
    description="The most widely used food colorant in the world. Class IV (E150d, sulfite ammonia caramel) is most common.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Class I (E150a, plain) is safe. Class IV (E150d) contains 4-MEI, classified as 'possibly carcinogenic' by IARC. California requires warning labels for products with >29 mcg 4-MEI per serving.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Listed color additive; no evidence of harm at current levels", year=2014)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="300 mg/kg bw/day (group ADI for caramel colors)",
                        source=Source(body="EFSA", title="Re-evaluation of caramel colours (E 150a-d)", year=2011)),
    ],
    health_effects=[
        "Class IV (E150d) contains 4-MEI — IARC 'possibly carcinogenic'",
        "California Prop 65 warning required above certain levels",
        "Class I (plain caramel, E150a) has no known safety issues",
        "Most commonly used colorant globally",
    ],
    common_products=["cola drinks", "soy sauce", "beer", "bread", "biscuits", "gravies"],
))

_register(IngredientInfo(
    name="Titanium Dioxide",
    aliases=["e171", "ins 171", "tio2", "ci 77891"],
    e_number="E171",
    ins_number="171",
    category=IngredientCategory.COLORANT,
    description="White pigment used to make food appear brighter/whiter. Used in candy coatings, sauces, and chewing gum.",
    concern_level=ConcernLevel.HIGH,
    concern_summary="Banned by EFSA/EU in 2022 due to genotoxicity concerns — cannot rule out DNA damage from nanoparticles. Still approved by FDA and FSSAI.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="100 ppm",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="1% by weight of food",
                        source=Source(body="FDA", title="21 CFR 73.575", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.BANNED,
                        source=Source(body="EFSA", title="Safety assessment of titanium dioxide (E 171) — can no longer be considered safe",
                                      url="https://www.efsa.europa.eu/en/efsajournal/pub/6585", year=2021)),
    ],
    sources=[
        Source(body="EFSA", title="EFSA: TiO2 can no longer be considered safe as food additive", url="https://www.efsa.europa.eu/en/news/titanium-dioxide-e-171-no-longer-considered-safe-when-used-food-additive", year=2021),
    ],
    health_effects=[
        "Banned in EU since 2022 due to genotoxicity concerns",
        "Nanoparticles may cross biological barriers",
        "EFSA: cannot rule out DNA damage",
        "Still approved by FDA and FSSAI",
        "Found in candy, chewing gum, coffee creamer, icing",
    ],
    common_products=["candy coating", "chewing gum", "coffee creamer", "icing", "toothpaste", "supplements"],
))

_register(IngredientInfo(
    name="Annatto",
    aliases=["e160b", "ins 160b", "bixin", "norbixin", "annatto extract", "annatto color"],
    e_number="E160b",
    ins_number="160b",
    category=IngredientCategory.COLORANT,
    description="Natural orange-red colorant from seeds of the achiote tree. Widely used in cheese and butter.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural plant-derived colorant used for centuries. Generally well-tolerated. Rare reports of allergic reactions.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Exempt from certification — natural color", year=2024)),
    ],
    health_effects=["Natural plant origin", "Very rare allergic reactions", "Generally safe"],
    common_products=["cheese", "butter", "margarine", "custard", "ice cream", "snack foods"],
))

_register(IngredientInfo(
    name="Paprika Oleoresin",
    aliases=["e160c", "ins 160c", "paprika extract", "capsanthin", "capsorubin"],
    e_number="E160c",
    ins_number="160c",
    category=IngredientCategory.COLORANT,
    description="Natural red-orange colorant extracted from paprika peppers.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Completely natural — extracted from paprika peppers. No safety concerns.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Exempt from certification — natural color", year=2024)),
    ],
    health_effects=["Natural pepper extract", "No safety concerns", "Contains carotenoids (antioxidants)"],
    common_products=["sausages", "cheese", "snack foods", "sauces", "soups"],
))

_register(IngredientInfo(
    name="Beta-Carotene",
    aliases=["e160a", "ins 160a", "beta carotene", "provitamin a", "carotene"],
    e_number="E160a",
    ins_number="160a",
    category=IngredientCategory.COLORANT,
    description="Natural orange pigment and precursor to vitamin A. Found in carrots, sweet potatoes, and mangoes.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Essential nutrient — body converts it to vitamin A. Found naturally in carrots. No safety concerns at food-use levels.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Exempt from certification — natural color", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="No safety concern at current food use", year=2012)),
    ],
    health_effects=["Precursor to vitamin A", "Antioxidant", "High-dose supplements may increase lung cancer risk in smokers (ATBC study)"],
    common_products=["margarine", "cheese", "beverages", "baked goods", "ice cream"],
))


# =====================================================================
# MORE SWEETENERS
# =====================================================================

_register(IngredientInfo(
    name="Saccharin",
    aliases=["e954", "ins 954", "saccharin sodium", "sodium saccharin", "sweet n low"],
    e_number="E954",
    ins_number="954",
    category=IngredientCategory.SWEETENER,
    description="Oldest artificial sweetener (discovered 1879). 300-500 times sweeter than sugar.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Was linked to bladder cancer in rats in the 1970s (led to warning labels), but the mechanism doesn't apply to humans. Delisted as carcinogen in 2000. Now considered safe.",
    adi="0-15 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Removed from NTP carcinogen list in 2000", year=2000)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="5 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Scientific Opinion on saccharin (E 954)", year=2009)),
    ],
    health_effects=[
        "Rat bladder cancer link debunked — mechanism doesn't occur in humans",
        "Delisted as carcinogen in 2000",
        "Bitter/metallic aftertaste at high concentrations",
    ],
    common_products=["diet drinks", "tabletop sweeteners", "medications", "toothpaste"],
))

_register(IngredientInfo(
    name="Erythritol",
    aliases=["e968", "ins 968"],
    e_number="E968",
    ins_number="968",
    category=IngredientCategory.SWEETENER,
    description="Sugar alcohol that occurs naturally in fruits. 60-70% as sweet as sugar with almost zero calories.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally well-tolerated (better than other sugar alcohols). A 2023 Cleveland Clinic study linked high blood levels to cardiovascular events, but this is debated.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS status", year=2001)),
    ],
    sources=[
        Source(body="PubMed", title="Witkowski et al. - The artificial sweetener erythritol and cardiovascular event risk", url="https://pubmed.ncbi.nlm.nih.gov/36854194/", year=2023),
    ],
    health_effects=[
        "2023 study linked high blood levels to heart attack/stroke risk (debated)",
        "Better tolerated than other sugar alcohols (less bloating)",
        "Almost zero calories",
        "Doesn't raise blood sugar — safe for diabetics",
    ],
    common_products=["sugar-free products", "keto products", "protein bars", "sugar-free chocolate"],
))

_register(IngredientInfo(
    name="Xylitol",
    aliases=["e967", "ins 967", "birch sugar"],
    e_number="E967",
    ins_number="967",
    category=IngredientCategory.SWEETENER,
    description="Sugar alcohol found naturally in birch bark and many fruits. About as sweet as sugar.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Well-studied and generally safe. Known to prevent dental cavities. Can cause digestive issues at high doses. Highly toxic to dogs.",
    adi="Not specified (JECFA considers acceptable at food-use levels)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Approved food additive", year=1986)),
    ],
    health_effects=[
        "Prevents dental cavities (WHO-endorsed for dental health)",
        "Can cause bloating, gas, diarrhea at >30g/day",
        "HIGHLY TOXIC TO DOGS — can be fatal",
        "Safe for diabetics — doesn't spike blood sugar",
    ],
    common_products=["sugar-free gum", "mints", "toothpaste", "sugar-free candy", "diabetic products"],
))

_register(IngredientInfo(
    name="Sorbitol",
    aliases=["e420", "ins 420", "d-sorbitol", "glucitol"],
    e_number="E420",
    ins_number="420",
    category=IngredientCategory.SWEETENER,
    description="Sugar alcohol naturally found in apples, pears, and stone fruits. About 60% as sweet as sugar.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally safe but has significant laxative effect at doses above 20g. Causes gas and bloating. Used in 'sugar-free' products.",
    adi="Not specified (laxation threshold is the limiting factor)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="21 CFR 184.1835", year=2024)),
    ],
    health_effects=[
        "Laxative effect above 20g/day",
        "Causes bloating, gas, and diarrhea at high intake",
        "Safe for diabetics — slowly absorbed",
        "Naturally found in stone fruits",
    ],
    common_products=["sugar-free candy", "sugar-free gum", "diabetic chocolate", "dried fruits", "toothpaste"],
))

_register(IngredientInfo(
    name="Neotame",
    aliases=["e961", "ins 961"],
    e_number="E961",
    ins_number="961",
    category=IngredientCategory.SWEETENER,
    description="Artificial sweetener 7,000-13,000 times sweeter than sugar. Derivative of aspartame but safe for PKU patients.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Very potent sweetener. Unlike aspartame, safe for people with PKU. Approved by all major regulators. Very little needed per serving.",
    adi="0-2 mg/kg body weight/day",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.APPROVED,
                        source=Source(body="FDA", title="Neotame approval", year=2002)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="2 mg/kg bw/day (ADI)",
                        source=Source(body="EFSA", title="Scientific Opinion on neotame (E 961)", year=2007)),
    ],
    health_effects=["Safe for PKU patients (unlike aspartame)", "Very potent — tiny amounts used", "No significant safety concerns"],
    common_products=["diet beverages", "sugar-free products", "baked goods", "tabletop sweeteners"],
))


# =====================================================================
# ANTI-CAKING AGENTS (common on chip bags, spice packets)
# =====================================================================

_register(IngredientInfo(
    name="Silicon Dioxide",
    aliases=["e551", "ins 551", "silica", "silicon dioxide (anti-caking agent)"],
    e_number="E551",
    ins_number="551",
    category=IngredientCategory.ANTI_CAKING_AGENT,
    description="Anti-caking agent used to prevent powders from clumping. Found naturally as quartz/sand.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Passes through the body unabsorbed. Used in salt, spices, and powdered foods. Very safe at food-use levels.",
    adi="Not specified (passes through body unabsorbed)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="10,000 ppm (1%) in most foods",
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        max_limit="2% by weight",
                        source=Source(body="FDA", title="21 CFR 172.480", year=2024)),
    ],
    health_effects=["Passes through body unabsorbed", "No safety concerns at food-use levels", "Different from industrial crystalline silica"],
    common_products=["salt", "spice mixes", "powdered sugar", "coffee creamer", "supplements", "chips seasoning"],
))

_register(IngredientInfo(
    name="Calcium Silicate",
    aliases=["e552", "ins 552"],
    e_number="E552",
    ins_number="552",
    category=IngredientCategory.ANTI_CAKING_AGENT,
    description="Anti-caking agent used in table salt and powdered foods.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Inert mineral compound. Passes through the body unabsorbed. Very safe.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        max_limit="2% by weight",
                        source=Source(body="FDA", title="21 CFR 182.2227", year=2024)),
    ],
    health_effects=["Inert — not absorbed by the body", "Very safe"],
    common_products=["table salt", "baking powder", "supplements"],
))


# =====================================================================
# COMMON NATURAL / WHOLE INGREDIENTS (people look these up too)
# =====================================================================

_register(IngredientInfo(
    name="Palm Oil",
    aliases=["refined palm oil", "palmolein", "palm olein", "rbd palm oil", "palm fat",
             "palm kernel oil", "vegetable fat (palm)"],
    category=IngredientCategory.FAT_OIL,
    description="Most widely used vegetable oil globally. Extracted from palm fruit. Major environmental and health debates.",
    concern_level=ConcernLevel.MODERATE,
    concern_summary="High in saturated fat (50%). WHO recommends limiting intake. Major environmental concern (deforestation). Contains 3-MCPD and glycidyl esters when refined at high temperatures.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted edible oil", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED,
                        source=Source(body="EFSA", title="Contaminants in palm oil: 3-MCPD and glycidyl esters concern", year=2016)),
    ],
    sources=[
        Source(body="WHO", title="WHO recommends limiting saturated fat to <10% of total energy", year=2018),
        Source(body="EFSA", title="Risks for human health related to the presence of 3- and 2-monochloropropanediol, and glycidyl esters in food", url="https://efsa.onlinelibrary.wiley.com/doi/abs/10.2903/j.efsa.2016.4426", year=2016),
    ],
    health_effects=[
        "50% saturated fat — raises LDL cholesterol",
        "Contains 3-MCPD and glycidyl esters (process contaminants) — EFSA flagged in 2016",
        "WHO: limit saturated fat to <10% of energy intake",
        "Major cause of tropical deforestation",
        "Cheaper than most other oils — dominates Indian processed food",
    ],
    common_products=["biscuits", "instant noodles", "chocolate", "margarine", "bread", "ice cream", "namkeen"],
))

_register(IngredientInfo(
    name="Whey Powder",
    aliases=["whey", "whey solids", "whey protein", "whey protein concentrate", "milk whey",
             "dried whey", "demineralized whey"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="Protein-rich byproduct of cheese making. Used as ingredient in baked goods, chocolates, and infant formula.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural dairy ingredient. Rich in protein. Allergen for those with milk/lactose intolerance.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted dairy ingredient", year=2011)),
    ],
    health_effects=["Allergen: contains milk proteins and lactose", "High-quality protein source", "Generally very safe"],
    common_products=["chocolates", "biscuits", "infant formula", "protein bars", "ice cream", "bread"],
))

_register(IngredientInfo(
    name="Milk Solids",
    aliases=["milk powder", "skimmed milk powder", "skim milk powder", "whole milk powder",
             "non-fat dry milk", "dried milk", "milk solids not fat", "msnf"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="Dried milk used as ingredient in thousands of food products.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural dairy ingredient. Allergen for those with milk allergy or lactose intolerance.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Dairy product standard", year=2011)),
    ],
    health_effects=["Allergen: milk proteins and lactose", "Good source of calcium and protein", "Safe"],
    common_products=["biscuits", "chocolate", "ice cream", "bread", "infant formula", "sweets"],
))

_register(IngredientInfo(
    name="Iodized Salt",
    aliases=["salt", "sodium chloride", "common salt", "table salt", "iodised salt", "refined salt",
             "sea salt", "rock salt", "sendha namak", "kala namak", "black salt"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="Essential mineral. Iodization is mandatory in India to prevent iodine deficiency disorders.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Essential in small amounts. WHO recommends <5g/day. Excess linked to hypertension. Iodization is mandatory in India under Prevention of Food Adulteration Act.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Iodization mandatory — minimum 15 ppm iodine at consumer level", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.WHO, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        max_limit="<5g/day recommended for adults",
                        source=Source(body="WHO", title="Guideline: Sodium intake for adults and children", url="https://www.who.int/publications/i/item/9789241504836", year=2012)),
    ],
    health_effects=[
        "WHO: limit to <5g/day (about 1 teaspoon)",
        "Excess raises blood pressure — hypertension risk",
        "Iodine prevents goiter and cretinism",
        "Essential mineral — needed for fluid balance",
    ],
    common_products=["virtually all processed and cooked food"],
))

_register(IngredientInfo(
    name="Edible Vegetable Oil",
    aliases=["vegetable oil", "edible oil", "soybean oil", "sunflower oil", "canola oil",
             "rapeseed oil", "cottonseed oil", "groundnut oil", "mustard oil",
             "rice bran oil", "safflower oil", "corn oil"],
    category=IngredientCategory.FAT_OIL,
    description="Generic term for plant-derived cooking oils used in food manufacturing.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Generally safe. Quality varies by extraction method (cold-pressed vs. refined). High omega-6 in some seed oils debated in nutrition science.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Standards for vegetable oils — specific rules per oil type", year=2011)),
    ],
    health_effects=[
        "Calorie-dense (9 kcal/g)",
        "Omega-6 to omega-3 ratio debated in nutrition science",
        "Cold-pressed oils retain more nutrients than refined",
        "Quality varies significantly by processing method",
    ],
    common_products=["cooking", "biscuits", "chips", "instant noodles", "namkeen", "fried foods"],
))

_register(IngredientInfo(
    name="Whole Wheat Flour",
    aliases=["atta", "whole wheat atta", "wholemeal flour", "wholegrain wheat flour",
             "chakki atta", "gehun ka atta", "wheat flour (whole)"],
    category=IngredientCategory.GRAIN_FLOUR,
    description="Flour made from whole wheat grain including bran, germ, and endosperm. Staple in Indian diet.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Nutritious whole grain. Good source of fiber, B vitamins, and minerals. Much healthier than refined flour (maida).",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Standards for wheat flour", year=2011)),
    ],
    sources=[
        Source(body="IFCT 2017", title="Indian Food Composition Tables — Whole wheat: 12.5g fiber/100g vs maida 0.3g", year=2017),
    ],
    health_effects=[
        "Good source of dietary fiber (12.5g/100g)",
        "Contains B vitamins, iron, zinc, magnesium",
        "Lower glycemic index than maida/refined flour",
        "Allergen: contains gluten",
    ],
    common_products=["roti", "chapati", "paratha", "bread", "biscuits", "noodles"],
))

_register(IngredientInfo(
    name="Jaggery",
    aliases=["gur", "gud", "panela", "unrefined cane sugar", "palm jaggery", "coconut jaggery"],
    category=IngredientCategory.SUGAR,
    description="Unrefined sugar made from sugarcane or palm sap. Traditional Indian sweetener.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Contains small amounts of minerals (iron, potassium) unlike white sugar, but still 65-85% sucrose. Often marketed as 'healthy sugar' which is somewhat misleading.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Standards for jaggery (gur)", year=2011)),
    ],
    sources=[
        Source(body="IFCT 2017", title="Jaggery: 383 kcal, 65-85% sucrose, 0.4g protein, iron 11mg/100g", year=2017),
    ],
    health_effects=[
        "65-85% sucrose — still a sugar",
        "Contains iron (11mg/100g), potassium, and other minerals",
        "Slightly lower glycemic index than white sugar",
        "Not a significant health food despite marketing",
        "Still raises blood sugar — problematic for diabetics",
    ],
    common_products=["Indian sweets", "gur ki chai", "laddoo", "chikki", "til gur"],
))

_register(IngredientInfo(
    name="Invert Sugar",
    aliases=["invert sugar syrup", "invert syrup", "inverted sugar"],
    category=IngredientCategory.SUGAR,
    description="Mixture of glucose and fructose made by heating sucrose with acid. Sweeter than table sugar.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Essentially the same as sugar (glucose + fructose). Used because it prevents crystallization. Same health concerns as regular sugar.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted sweetener", year=2011)),
    ],
    health_effects=[
        "Same as regular sugar — contributes to obesity, diabetes, tooth decay",
        "Sweeter than sucrose — slightly less needed per serving",
        "Prevents crystallization in confectionery",
    ],
    common_products=["biscuits", "cakes", "confectionery", "ice cream", "beverages", "honey substitutes"],
))

_register(IngredientInfo(
    name="Liquid Glucose",
    aliases=["glucose syrup", "corn syrup", "glucose", "dextrose syrup", "starch syrup"],
    category=IngredientCategory.SUGAR,
    description="Thick syrup made from starch hydrolysis. Used widely in confectionery and baked goods.",
    concern_level=ConcernLevel.LOW,
    concern_summary="High glycemic index. Essentially a liquid form of sugar derived from starch. Less sweet than sucrose but still spikes blood sugar.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted sweetener", year=2011)),
    ],
    health_effects=[
        "High glycemic index",
        "Spikes blood sugar rapidly",
        "Contributes to obesity and tooth decay",
        "Less sweet than sucrose — more needed to achieve same sweetness",
    ],
    common_products=["candy", "ice cream", "baked goods", "sauces", "sports drinks", "Indian sweets"],
))


# =====================================================================
# FLAVOR ENHANCERS (common in chips, instant noodles)
# =====================================================================

_register(IngredientInfo(
    name="Disodium Guanylate",
    aliases=["e627", "ins 627", "sodium guanylate", "gmp"],
    e_number="E627",
    ins_number="627",
    category=IngredientCategory.FLAVOR_ENHANCER,
    description="Flavor enhancer that works synergistically with MSG. Derived from nucleotides.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally safe. Often used with MSG to enhance umami taste. Not recommended for people with gout (contains purines).",
    adi="Not specified (safe at current food-use levels)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS status", year=2024)),
    ],
    health_effects=[
        "Contains purines — avoid if you have gout or uric acid issues",
        "Usually used with MSG — synergistic umami effect",
        "Generally safe at food-use levels",
    ],
    common_products=["chips", "instant noodles", "snack foods", "soups", "sauces", "processed meats"],
))

_register(IngredientInfo(
    name="Disodium Inosinate",
    aliases=["e631", "ins 631", "sodium inosinate", "imp"],
    e_number="E631",
    ins_number="631",
    category=IngredientCategory.FLAVOR_ENHANCER,
    description="Flavor enhancer that enhances umami taste. Often paired with MSG and disodium guanylate.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally safe. Like E627, contains purines — not suitable for gout patients. Almost always used alongside MSG.",
    adi="Not specified (safe at current food-use levels)",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS status", year=2024)),
    ],
    health_effects=[
        "Contains purines — avoid with gout",
        "Usually combined with MSG and E627",
        "Generally safe",
    ],
    common_products=["chips", "instant noodles", "snack foods", "cup noodles", "seasonings"],
))

_register(IngredientInfo(
    name="Disodium 5'-Ribonucleotides",
    aliases=["e635", "ins 635", "i+g", "flavor enhancer 635"],
    e_number="E635",
    ins_number="635",
    category=IngredientCategory.FLAVOR_ENHANCER,
    description="Mixture of disodium inosinate and disodium guanylate. The most common MSG companion.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Combination of E627 and E631. Same safety profile — avoid with gout. Very commonly seen on Indian chip and noodle packets.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="GRAS status", year=2024)),
    ],
    health_effects=["Contains purines — avoid with gout", "Synergistic with MSG", "Generally safe"],
    common_products=["Lay's chips", "Maggi noodles", "Kurkure", "instant soups", "namkeen"],
))

_register(IngredientInfo(
    name="Hydrolyzed Vegetable Protein",
    aliases=["hvp", "hydrolysed vegetable protein", "hydrolyzed soy protein",
             "hydrolyzed plant protein", "hydrolysed soy protein"],
    category=IngredientCategory.FLAVOR_ENHANCER,
    description="Protein broken down into amino acids for umami flavor. Contains naturally occurring MSG.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Contains free glutamic acid (natural MSG). Used as a flavoring. May contain 3-MCPD (process contaminant) if produced with HCl.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Permitted flavoring", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="Must be labeled — contains free glutamate", year=2024)),
    ],
    health_effects=[
        "Contains free glutamic acid (natural MSG)",
        "May contain 3-MCPD process contaminant",
        "Allergen risk if derived from soy or wheat",
    ],
    common_products=["instant noodle seasoning", "soups", "sauces", "snack seasonings", "gravy mixes"],
))

_register(IngredientInfo(
    name="Yeast Extract",
    aliases=["autolyzed yeast extract", "hydrolyzed yeast extract", "yeast autolysate",
             "yeast extract powder"],
    category=IngredientCategory.FLAVOR_ENHANCER,
    description="Concentrated flavor from yeast cell contents. Natural source of umami (glutamic acid).",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural flavoring. Contains free glutamic acid (like aged cheese and tomatoes). Used to avoid listing 'MSG' on labels.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Natural flavoring ingredient", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="Natural flavoring — but must not be labeled as 'no MSG added' if used", year=2024)),
    ],
    health_effects=[
        "Contains free glutamic acid (natural MSG)",
        "May trigger MSG-like symptoms in sensitive individuals",
        "Not technically MSG but has similar effects",
    ],
    common_products=["chips", "soups", "sauces", "processed foods", "stock cubes", "Marmite/Vegemite"],
))


# =====================================================================
# HUMECTANTS & STABILIZERS
# =====================================================================

_register(IngredientInfo(
    name="Glycerol",
    aliases=["e422", "ins 422", "glycerin", "glycerine", "vegetable glycerin"],
    e_number="E422",
    ins_number="422",
    category=IngredientCategory.HUMECTANT,
    description="Sweet-tasting sugar alcohol used to retain moisture in foods.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Naturally occurs in all fats and oils. Very safe. Used in food, pharmaceuticals, and cosmetics for centuries.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.1320", year=2024)),
    ],
    health_effects=["Naturally occurs in all fats", "Very safe", "Mild laxative effect at very high doses"],
    common_products=["protein bars", "soft candy", "baked goods", "ice cream", "marshmallows"],
))

_register(IngredientInfo(
    name="Pectin",
    aliases=["e440", "ins 440", "fruit pectin", "apple pectin", "citrus pectin"],
    e_number="E440",
    ins_number="440",
    category=IngredientCategory.THICKENER,
    description="Natural polysaccharide found in fruit cell walls. Used to gel jams and jellies.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Completely natural — found in all fruits (especially apples and citrus peels). Also a dietary fiber. Very safe.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1588", year=2024)),
    ],
    health_effects=["Natural fruit component", "Dietary fiber — aids digestion", "May lower cholesterol", "Very safe"],
    common_products=["jams", "jellies", "marmalades", "fruit juices", "yogurt", "gummy candy"],
))

_register(IngredientInfo(
    name="Sodium Carboxymethyl Cellulose",
    aliases=["e466", "ins 466", "cmc", "cellulose gum", "carboxymethylcellulose"],
    e_number="E466",
    ins_number="466",
    category=IngredientCategory.THICKENER,
    description="Cellulose derivative used as thickener and stabilizer in ice cream, sauces, and beverages.",
    concern_level=ConcernLevel.LOW,
    concern_summary="Generally safe. Some animal studies suggest it may promote intestinal inflammation (like other synthetic emulsifiers), but evidence is limited in humans.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.1745", year=2024)),
        RegulatoryEntry(body=RegulatoryBody.EFSA, status=ApprovalStatus.APPROVED_WITH_LIMITS,
                        source=Source(body="EFSA", title="Re-evaluation of celluloses (E 460-466)", year=2018)),
    ],
    health_effects=[
        "Some animal studies link to gut inflammation",
        "Generally safe at approved levels",
        "Not absorbed by the body",
    ],
    common_products=["ice cream", "sauces", "salad dressings", "beverages", "gluten-free products"],
))

_register(IngredientInfo(
    name="Sodium Alginate",
    aliases=["e401", "ins 401", "alginic acid sodium salt", "algin"],
    e_number="E401",
    ins_number="401",
    category=IngredientCategory.THICKENER,
    description="Natural thickener and gelling agent from brown seaweed. Used in ice cream and sauces.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Natural seaweed extract. Very safe. Also used in wound dressings and dental impressions.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 184.1724", year=2024)),
    ],
    health_effects=["Natural seaweed origin", "Dietary fiber", "Very safe"],
    common_products=["ice cream", "jelly", "sauces", "beer", "pet food"],
))

_register(IngredientInfo(
    name="Agar",
    aliases=["e406", "ins 406", "agar-agar", "china grass", "japanese gelatin"],
    e_number="E406",
    ins_number="406",
    category=IngredientCategory.THICKENER,
    description="Natural gelling agent from red seaweed. Vegetarian alternative to gelatin.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Completely natural seaweed product. Used in Indian and Asian cooking for centuries. Popular vegetarian/vegan gelatin substitute.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Additives Regulations, 2011", year=2011)),
        RegulatoryEntry(body=RegulatoryBody.FDA, status=ApprovalStatus.GRAS,
                        source=Source(body="FDA", title="21 CFR 182.1115", year=2024)),
    ],
    health_effects=["Natural seaweed product", "Dietary fiber", "May aid digestion", "Vegetarian/vegan friendly"],
    common_products=["desserts", "jellies", "ice cream", "canned meats", "Asian sweets"],
))


# =====================================================================
# VITAMINS & MINERALS (fortification — common on Indian labels)
# =====================================================================

_register(IngredientInfo(
    name="Ferrous Fumarate",
    aliases=["iron", "iron fortification", "ferrous sulfate", "ferric pyrophosphate",
             "reduced iron", "iron (as ferrous fumarate)"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="Iron supplement used to fortify foods. FSSAI mandates wheat flour fortification in India.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Essential micronutrient. Iron deficiency is the most common nutritional deficiency globally. FSSAI mandates iron fortification of wheat flour.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Food Fortification Regulations, 2018 — mandatory for wheat flour", year=2018)),
    ],
    health_effects=["Essential nutrient", "Prevents anemia", "Excess can cause constipation and stomach upset"],
    common_products=["fortified wheat flour", "breakfast cereals", "bread", "infant formula"],
))

_register(IngredientInfo(
    name="Folic Acid",
    aliases=["vitamin b9", "folate", "pteroylglutamic acid", "folic acid (vitamin b9)"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="B vitamin essential for cell division. Mandatory fortification in wheat flour in India.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Essential vitamin. Prevents neural tube defects in pregnancy. FSSAI-mandated in wheat flour fortification.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Mandatory fortification of wheat flour", year=2018)),
    ],
    health_effects=["Prevents neural tube defects in pregnancy", "Essential for DNA synthesis", "Very safe"],
    common_products=["fortified flour", "cereals", "bread", "supplements"],
))

_register(IngredientInfo(
    name="Vitamin A",
    aliases=["retinol", "retinyl palmitate", "beta-carotene", "vitamin a palmitate",
             "retinyl acetate"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="Fat-soluble vitamin essential for vision and immunity. Used in food fortification.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Essential vitamin. FSSAI mandates fortification of edible oils and milk. Toxic only at very high supplement doses.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Mandatory fortification of edible oils and milk", year=2018)),
    ],
    health_effects=["Essential for vision and immunity", "Toxic at very high doses (hypervitaminosis A)", "Safe at fortification levels"],
    common_products=["fortified oils", "fortified milk", "margarine", "cereals", "supplements"],
))

_register(IngredientInfo(
    name="Vitamin D",
    aliases=["vitamin d2", "vitamin d3", "cholecalciferol", "ergocalciferol",
             "vitamin d (cholecalciferol)"],
    category=IngredientCategory.NATURAL_INGREDIENT,
    description="Fat-soluble vitamin essential for calcium absorption and bone health.",
    concern_level=ConcernLevel.NONE,
    concern_summary="Essential vitamin. Widespread deficiency in India (70-90% of population). FSSAI mandates fortification of milk and edible oils.",
    regulatory=[
        RegulatoryEntry(body=RegulatoryBody.FSSAI, status=ApprovalStatus.APPROVED,
                        source=Source(body="FSSAI", title="Mandatory fortification of milk and edible oils", year=2018)),
    ],
    health_effects=["Essential for bone health", "70-90% of Indians are deficient", "Toxic only at very high doses"],
    common_products=["fortified milk", "fortified oils", "cereals", "supplements", "fortified bread"],
))
