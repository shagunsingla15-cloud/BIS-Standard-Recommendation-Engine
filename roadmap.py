"""roadmap.py — Compliance Roadmap Generator"""

ROADMAP_TEMPLATES = {
    "Cement": [
        "1. Obtain samples per {sampling} — minimum lot size and sample quantity",
        "2. Conduct physical tests per {testing} — fineness, setting time, soundness",
        "3. Conduct compressive strength tests at 3, 7, 28 days per {testing}",
        "4. Verify chemical composition (C3S, C3A, SO3) as per {standard_id} Table 1",
        "5. Engage BIS-licensed laboratory for third-party verification",
        "6. Apply for ISI Mark License from BIS Regional Office",
        "7. Maintain test records for 3 years post-supply"
    ],
    "Steel": [
        "1. Sample bars per {sampling} — one sample per 25-tonne lot",
        "2. Conduct tensile test per {testing} — yield stress, UTS, elongation",
        "3. Conduct bend/re-bend test per {testing}",
        "4. Verify rib geometry and nominal diameter against {standard_id} Table",
        "5. Check mill test certificate (MTC) from steel producer",
        "6. Verify ISI Mark on each bundle tag",
        "7. Store test coupons for at least 90 days"
    ],
    "Masonry": [
        "1. Sample masonry units per {sampling} — 10 units per 10,000 lot",
        "2. Test compressive strength per {testing}",
        "3. Test water absorption (24-hour immersion) per {testing}",
        "4. Check dimensions and tolerances per {standard_id}",
        "5. Test efflorescence (for clay bricks) per {testing}",
        "6. Verify BIS certification mark on delivery challan",
    ],
    "Waterproofing": [
        "1. Verify product composition matches {standard_id} chemical requirements",
        "2. Conduct compatibility test with site cement grade",
        "3. Apply trial patch as per manufacturer and {standard_id} specification",
        "4. Test water permeability per {testing}",
        "5. Obtain technical data sheet confirming IS compliance",
        "6. Document application method and curing protocol"
    ],
    "Testing": [
        "1. This is a testing/sampling standard — apply to primary material",
        "2. Ensure lab is NABL-accredited for relevant test methods",
        "3. Maintain calibration records for all testing equipment"
    ],
    "Aggregates": [
        "1. Sample aggregates per {sampling}",
        "2. Conduct sieve analysis per {testing}",
        "3. Test for deleterious materials (silt, organic matter) per {testing}",
        "4. Test aggregate crushing value, impact value per {testing}",
        "5. Verify grading zone matches design mix requirement",
    ],
    "Finishing": [
        "1. Sample boards per {standard_id} sampling clause",
        "2. Test flexural strength (dry and wet) per {standard_id}",
        "3. Verify dimensions and squareness tolerances",
        "4. Check surface finish and edge quality",
        "5. Obtain BIS or manufacturer's compliance certificate"
    ]
}

class ComplianceRoadmapGenerator:
    def generate(self, result: dict) -> list:
        category = result.get("category", "Testing")
        template = ROADMAP_TEMPLATES.get(category, ROADMAP_TEMPLATES["Testing"])
        testing = ", ".join(result.get("testing_standards", [])) or "applicable IS method"
        sampling = ", ".join(result.get("sampling_standards", [])) or "applicable IS sampling"
        standard_id = result.get("standard_id", "")

        roadmap = []
        for step in template:
            roadmap.append(
                step.format(
                    testing=testing,
                    sampling=sampling,
                    standard_id=standard_id
                )
            )
        return roadmap
