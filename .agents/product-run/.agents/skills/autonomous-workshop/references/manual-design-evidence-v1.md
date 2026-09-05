# Manual design evidence v1

New manual-first runs require canonical
`artifacts/release/package/MANUAL-DESIGN.json`. It proves that the native
Release Goal performed the product-specific design and review workflow; it is
not a host-authored aesthetic score.

Use exactly this top-level shape:

```json
{
  "schema_version": 1,
  "kind": "autonomous-workshop.manual-design-evidence",
  "manual_sha256": "<exact MANUAL.pdf sha256>",
  "design_mode": "bespoke",
  "creative_brief": {
    "emotional_promise": "<20-500 characters>",
    "physical_format": "<3-200 characters>",
    "format_rationale": "<20-1000 characters>",
    "visual_motif": "<20-500 characters>",
    "palette": ["<3-8 unique entries>"],
    "typography": ["<2-6 unique role/family entries>"],
    "teaching_arc": ["<3-12 unique instructional beats>"]
  },
  "product_visuals": [
    {
      "source_path": "<exact path in the sealed Made manifest>",
      "source_sha256": "<exact Made entry sha256>",
      "pages": [1]
    }
  ],
  "review": {
    "page_count": 2,
    "color_pages": [1, 2],
    "grayscale_pages": [1, 2],
    "first_time_owner_pass": true,
    "independent_reviewer": "native-subagent",
    "findings": ["<at least one concrete independent finding>"],
    "resolved_changes": ["<at least one concrete revision made>"],
    "status": "approved"
  }
}
```

Rules:

- Canonical JSON is UTF-8 with sorted object keys, compact separators, finite
  values, no duplicate keys, and no trailing newline.
- `manual_sha256` identifies the final PDF after every revision.
- Every `product_visuals` entry must name an image or model byte in the exact
  sealed Made manifest and repeat its hash, or one host render exactly as
  `STAGE.json.host_renders.outputs[]` lists it (`source_path` =
  `manual_source_path`, for example `renders/hero.png`, and `source_sha256` =
  its `sha256`). Page lists are sorted, unique, one-based, and within the
  final PDF. The union must include page 1.
- `color_pages` and `grayscale_pages` each list every page exactly once in
  ascending order. Inspect the actual renders at intended print size.
- Use embedded fonts only. Standard PDF base fonts and operating-system
  fallbacks do not satisfy the evidence gate.
- The independent native subagent reviews the first complete render. Do not
  supply the intended verdict or conceal known weaknesses. Record concise
  findings and the actual changes resolved before approval.
- Keep internal reasoning, prompts, transcripts, credentials, and host state
  out of the evidence file.
