# Mechanical fidelity / verification status

No variant in this release is **certified accurate** to a specific physical PCB revision. Numeric model coordinates should not be presented as measured vendor PCB coordinates.

- **11 reference configurations:** six single-relay, plus 2/4/6/8/16 relays.
- **22 meshes:** one PCB with mounting apertures, one illustrative full assembly per configuration.
- **Coordinate and envelope values:** `data/ALL_FEATURE_COORDINATES.csv`, `data/accuracy_sources.json`.
- **Sources:** public factual specifications (external hyperlinks in `data/accuracy_sources.json`); not manufacturer CAD imported into this release.
- **Mesh QA:** topology and modeled component/nominal-hole collision checks in `data/QA_REPORT.json`. QA is not experimental confirmation of real dimensions.

| Class | Interpretation | Recommended use |
|---|---|---|
| C — Nominal board outline and/or mounting pitch | From stated product specification, not independently measured on an identified hardware revision | Preliminary enclosure layout only |
| D — Geometric reconstruction | Component center or envelope inferred to form a plausible mechanical proxy | Visualization / rough clearance only |
| E — Unverified estimate | Unconfirmed hole centers, hole diameter, height, or package footprint | Must not be machined against without measurement |

**No variant has Class A (verified against factory PCB source for that exact product revision) or Class B (measured physical board with tolerance record).** Even classes C–E vary by feature within one variant; inspect individual CSV evidence notes rather than assigning one precision grade to the entire board.

For mains switching, the geometry does **not** provide creepage, clearance, isolation or thermal safety documentation. Do not infer a safe case design solely from these STL models.
