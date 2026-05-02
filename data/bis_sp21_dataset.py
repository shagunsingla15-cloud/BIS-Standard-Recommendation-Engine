# data/bis_sp21_dataset.py
# BIS SP 21 (Building Materials) - Source of Truth Dataset
# This is the ONLY data source used for retrieval — prevents hallucinations.

BIS_STANDARDS = [
    {
        "standard_id": "IS 269",
        "title": "Ordinary Portland Cement, 33 Grade — Specification",
        "category": "Cement",
        "summary": "Specifies requirements for 33-grade ordinary Portland cement used in general construction. Covers chemical composition, physical properties including fineness, setting time, and compressive strength.",
        "keywords": ["cement", "OPC", "ordinary portland", "33 grade", "binder", "concrete"],
        "clause_refs": ["Cl.4 Chemical Requirements", "Cl.5 Physical Requirements"],
        "testing_deps": ["IS 4031", "IS 1727"],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 8112",
        "title": "Ordinary Portland Cement, 43 Grade — Specification",
        "category": "Cement",
        "summary": "Specifies 43-grade OPC for general structural use where higher early strength is needed. Suitable for RCC, precast, and pre-stressed work.",
        "keywords": ["cement", "OPC", "43 grade", "high strength", "RCC", "structural"],
        "clause_refs": ["Cl.4 Chemical", "Cl.5 Physical", "Cl.6 Soundness"],
        "testing_deps": ["IS 4031"],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 12269",
        "title": "Ordinary Portland Cement, 53 Grade — Specification",
        "category": "Cement",
        "summary": "High-strength OPC 53-grade for bridges, high-rise buildings, marine structures, and prestressed concrete. Requires low water-cement ratio.",
        "keywords": ["cement", "53 grade", "high rise", "bridge", "marine", "prestressed", "high strength cement"],
        "clause_refs": ["Cl.4 Chemical Requirements", "Cl.5.1 Fineness", "Cl.5.3 Compressive Strength"],
        "testing_deps": ["IS 4031", "IS 650"],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 1489",
        "title": "Portland Pozzolana Cement — Specification",
        "category": "Cement",
        "summary": "Blended cement using fly ash or calcined clay pozzolana. Suitable for mass concrete, marine works, hydraulic structures, and where sulfate attack is a concern.",
        "keywords": ["PPC", "pozzolana", "fly ash", "blended cement", "sulfate resistant", "hydraulic", "mass concrete"],
        "clause_refs": ["Part 1: Fly Ash Based", "Part 2: Calcined Clay Based"],
        "testing_deps": ["IS 4031"],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 455",
        "title": "Portland Slag Cement — Specification",
        "category": "Cement",
        "summary": "Cement made with granulated blast furnace slag. Suitable for underground structures, marine works, mass concrete dams, and foundation work in sulfate-bearing soils.",
        "keywords": ["slag cement", "PSC", "blast furnace", "sulfate soil", "underground", "foundation"],
        "clause_refs": ["Cl.4", "Cl.5"],
        "testing_deps": ["IS 4031"],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 432",
        "title": "Mild Steel and Medium Tensile Steel Bars for Concrete Reinforcement",
        "category": "Steel",
        "summary": "Specification for mild steel (Grade I) and medium tensile steel bars used as reinforcement in concrete structures. Covers yield stress, tensile strength, and elongation.",
        "keywords": ["mild steel", "TMT bar", "reinforcement bar", "rebar", "concrete reinforcement", "steel bar"],
        "clause_refs": ["Cl.5 Mechanical Properties", "Cl.6 Dimensions"],
        "testing_deps": ["IS 1608", "IS 1599"],
        "sampling_deps": ["IS 4711"]
    },
    {
        "standard_id": "IS 1786",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        "category": "Steel",
        "summary": "Covers Fe 415, Fe 500, Fe 550, Fe 600 grade HYSD/TMT bars. Standard for modern RCC construction. Specifies rib geometry, yield strength, UTS, and bend/re-bend tests.",
        "keywords": ["HYSD", "TMT bar", "Fe 415", "Fe 500", "Fe 550", "deformed bar", "high strength steel", "reinforcement"],
        "clause_refs": ["Cl.5 Chemical Composition", "Cl.6 Mechanical Properties", "Cl.7 Bend Test"],
        "testing_deps": ["IS 1608", "IS 1599"],
        "sampling_deps": ["IS 4711"]
    },
    {
        "standard_id": "IS 2062",
        "title": "Hot Rolled Medium and High Tensile Structural Steel",
        "category": "Steel",
        "summary": "Structural steel for general construction, bridges, and industrial structures. Grades E250, E300, E350, E410. Covers plates, strips, shapes, and sections.",
        "keywords": ["structural steel", "MS plate", "HR plate", "E250", "E350", "I-beam", "channel section"],
        "clause_refs": ["Cl.5 Chemical Composition", "Cl.6 Mechanical Properties"],
        "testing_deps": ["IS 1608"],
        "sampling_deps": ["IS 4711"]
    },
    {
        "standard_id": "IS 516",
        "title": "Method of Tests for Strength of Concrete",
        "category": "Testing",
        "summary": "Defines methods for testing compressive strength, flexural strength, and splitting tensile strength of concrete specimens.",
        "keywords": ["concrete test", "compressive strength", "cube test", "flexural test"],
        "clause_refs": ["Cl.5 Compressive Strength", "Cl.6 Flexural Strength"],
        "testing_deps": [],
        "sampling_deps": ["IS 1199"]
    },
    {
        "standard_id": "IS 383",
        "title": "Coarse and Fine Aggregate for Concrete — Specification",
        "category": "Aggregates",
        "summary": "Specifies natural aggregates (sand, gravel, crushed stone) for concrete. Covers grading zones, silt content, organic impurities, and soundness.",
        "keywords": ["aggregate", "sand", "gravel", "crushed stone", "coarse aggregate", "fine aggregate", "concrete mix"],
        "clause_refs": ["Cl.4 Grading", "Cl.5 Deleterious Materials"],
        "testing_deps": ["IS 2386"],
        "sampling_deps": ["IS 2430"]
    },
    {
        "standard_id": "IS 2386",
        "title": "Methods of Test for Aggregates for Concrete",
        "category": "Testing",
        "summary": "Testing methods for particle size, shape, surface texture, water absorption, and soundness of aggregates used in concrete.",
        "keywords": ["aggregate test", "particle size", "sieve analysis", "flakiness index"],
        "clause_refs": ["Part 1-8"],
        "testing_deps": [],
        "sampling_deps": ["IS 2430"]
    },
    {
        "standard_id": "IS 3025",
        "title": "Methods of Sampling and Test (Physical and Chemical) for Water Used in Industry",
        "category": "Testing",
        "summary": "Specifies acceptable quality of water for construction mixing. Covers pH, sulfate content, chloride content, and turbidity.",
        "keywords": ["water quality", "mixing water", "chloride", "sulfate", "pH water", "construction water"],
        "clause_refs": ["Cl.4 Physical Tests", "Cl.5 Chemical Tests"],
        "testing_deps": [],
        "sampling_deps": []
    },
    {
        "standard_id": "IS 2645",
        "title": "Integral Cement Waterproofing Compounds — Specification",
        "category": "Waterproofing",
        "summary": "Covers waterproofing admixtures added to cement for water-retaining structures, roofs, basements. Includes chemical and physical requirements.",
        "keywords": ["waterproofing", "admixture", "waterproof cement", "basement", "roof waterproofing", "integral waterproofing"],
        "clause_refs": ["Cl.4 Requirements", "Cl.5 Tests"],
        "testing_deps": ["IS 4031"],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 2250",
        "title": "Code of Practice for Preparation and Use of Masonry Mortars",
        "category": "Masonry",
        "summary": "Covers mix proportions and workmanship for cement, lime, and mixed mortars for brickwork, blockwork, and stone masonry.",
        "keywords": ["mortar", "masonry mortar", "brick mortar", "cement mortar", "lime mortar", "plastering"],
        "clause_refs": ["Cl.5 Mix Proportions", "Cl.6 Application"],
        "testing_deps": ["IS 4031"],
        "sampling_deps": []
    },
    {
        "standard_id": "IS 1077",
        "title": "Common Burnt Clay Building Bricks — Specification",
        "category": "Masonry",
        "summary": "Specifies dimensions, compressive strength, water absorption, and efflorescence for common burnt clay bricks. Classes 3.5 to 35.",
        "keywords": ["brick", "clay brick", "burnt brick", "red brick", "masonry brick", "wall brick"],
        "clause_refs": ["Cl.4 Dimensions", "Cl.5 Compressive Strength", "Cl.6 Water Absorption"],
        "testing_deps": ["IS 3495"],
        "sampling_deps": ["IS 5454"]
    },
    {
        "standard_id": "IS 2185",
        "title": "Concrete Masonry Units — Specification",
        "category": "Masonry",
        "summary": "Covers hollow and solid concrete blocks for load-bearing and non-load-bearing walls. Specifies dimensions, density, compressive strength.",
        "keywords": ["concrete block", "hollow block", "AAC block", "masonry unit", "cement block", "wall block"],
        "clause_refs": ["Cl.4 Types", "Cl.5 Dimensions", "Cl.6 Strength"],
        "testing_deps": ["IS 2185 Part Tests"],
        "sampling_deps": ["IS 4905"]
    },
    {
        "standard_id": "IS 2095",
        "title": "Gypsum Plaster Boards — Specification",
        "category": "Finishing",
        "summary": "Covers gypsum-based board for internal partitions and ceilings. Specifies dimensions, flexural strength, and moisture resistance.",
        "keywords": ["gypsum board", "drywall", "partition board", "false ceiling", "plaster board", "gypsum panel"],
        "clause_refs": ["Cl.4 Types", "Cl.5 Dimensions", "Cl.6 Physical Requirements"],
        "testing_deps": ["IS 2542"],
        "sampling_deps": []
    },
    {
        "standard_id": "IS 1346",
        "title": "Code of Practice for Waterproofing of Roofs with Bitumen Felts",
        "category": "Waterproofing",
        "summary": "Covers waterproofing systems for flat roofs using bituminous felts, including preparation, application, and protection layers.",
        "keywords": ["bitumen felt", "roof waterproofing", "flat roof", "bituminous membrane", "terrace waterproofing"],
        "clause_refs": ["Cl.5 Materials", "Cl.6 Application"],
        "testing_deps": ["IS 1322"],
        "sampling_deps": []
    },
    {
        "standard_id": "IS 4031",
        "title": "Methods of Physical Tests for Hydraulic Cement",
        "category": "Testing",
        "summary": "Standard testing methods for all hydraulic cements covering fineness, soundness, setting time, and compressive strength at 3, 7, 28 days.",
        "keywords": ["cement test", "physical test", "fineness test", "setting time", "soundness test", "Vicat needle"],
        "clause_refs": ["Part 1-15"],
        "testing_deps": [],
        "sampling_deps": ["IS 3535"]
    },
    {
        "standard_id": "IS 3535",
        "title": "Methods of Sampling Hydraulic Cements",
        "category": "Sampling",
        "summary": "Procedures for sampling cement from bulk storage, bags, and tankers for quality testing. Defines lot size and sample quantity.",
        "keywords": ["cement sampling", "lot sampling", "sampling procedure"],
        "clause_refs": ["Cl.4 Sampling Methods"],
        "testing_deps": [],
        "sampling_deps": []
    }
]

# Dependency graph lookup (standard_id -> related testing/sampling standards)
DEPENDENCY_GRAPH = {
    "IS 269":  {"testing": ["IS 4031", "IS 1727"], "sampling": ["IS 3535"]},
    "IS 8112": {"testing": ["IS 4031"],             "sampling": ["IS 3535"]},
    "IS 12269":{"testing": ["IS 4031", "IS 650"],   "sampling": ["IS 3535"]},
    "IS 1489": {"testing": ["IS 4031"],             "sampling": ["IS 3535"]},
    "IS 455":  {"testing": ["IS 4031"],             "sampling": ["IS 3535"]},
    "IS 432":  {"testing": ["IS 1608", "IS 1599"],  "sampling": ["IS 4711"]},
    "IS 1786": {"testing": ["IS 1608", "IS 1599"],  "sampling": ["IS 4711"]},
    "IS 2062": {"testing": ["IS 1608"],             "sampling": ["IS 4711"]},
    "IS 383":  {"testing": ["IS 2386"],             "sampling": ["IS 2430"]},
    "IS 1077": {"testing": ["IS 3495"],             "sampling": ["IS 5454"]},
    "IS 2185": {"testing": ["IS 2185"],             "sampling": ["IS 4905"]},
    "IS 2645": {"testing": ["IS 4031"],             "sampling": ["IS 3535"]},
    "IS 1346": {"testing": ["IS 1322"],             "sampling": []},
}

# Vagueness detection patterns → clarifying questions
VAGUENESS_RULES = [
    {
        "triggers": ["cement", "concrete"],
        "context_missing": ["grade", "53", "43", "33", "OPC", "PPC", "PSC"],
        "question": "What grade and type of cement is required? (e.g., OPC 43/53, PPC for marine use, PSC for sulfate soil)"
    },
    {
        "triggers": ["steel bar", "rebar", "reinforcement"],
        "context_missing": ["Fe 415", "Fe 500", "Fe 550", "grade", "TMT", "mild"],
        "question": "What grade of reinforcement bar is needed? (e.g., Fe 415 for standard RCC, Fe 500/550 for seismic zones)"
    },
    {
        "triggers": ["waterproof", "waterproofing"],
        "context_missing": ["roof", "basement", "underground", "integral", "membrane", "bitumen"],
        "question": "What type of waterproofing is required? (e.g., integral admixture for concrete, bitumen membrane for flat roof, basement tanking)"
    },
    {
        "triggers": ["coastal", "marine", "corrosion"],
        "context_missing": ["zone", "grade", "exposure"],
        "question": "Is this for a coastal (high chloride) or inland environment? This affects the cement type and steel grade selection."
    },
    {
        "triggers": ["brick", "block", "masonry"],
        "context_missing": ["clay", "concrete", "AAC", "load bearing", "partition", "hollow"],
        "question": "Is this for load-bearing masonry or partition walls? And what material — burnt clay brick, concrete block, or AAC block?"
    }
]
