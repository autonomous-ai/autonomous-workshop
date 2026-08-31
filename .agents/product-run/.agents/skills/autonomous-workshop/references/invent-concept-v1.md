# Active Invent Concept boundary v1

This immutable capability activates Concept only as a compound sub-boundary of
Forge and Quest Invent. The existing Invent Goal and native turn select the
Inventor, seal the invention, and author the complete pre-render Concept
source. After that turn exits, the trusted Workshop host alone validates the
source, performs any authorized durable image effect, seals the exact returned
bytes, and advances the one Invent gate directly to Make.

The capability never adds a Concept stage, Goal, turn, checkpoint, transition,
or status value. Spark has no Invent stage and does not activate this boundary.
Runs that did not freeze these exact bytes retain their prior protocol.

Concept research and images are design instruction, not product, Playtest,
manufacture, publication, delivery, or physical evidence. Provider credentials
and private effect state remain host-only.

When `STAGE.json.inputs.invent_concept_capability` binds these exact bytes, the
Manager and selected Inventor must author, at the packet-named `concept_root`,
exactly these five JSON files before the one Invent finalizer call:

- `brief.json`: decided object/category, envelope, wall thickness, print
  stance, distinctive features, fit target, stable component keys with exact
  form/dimensions/placement/interfaces, and one source-or-decision attribution
  for every required fact;
- `research.json`: bounded sources with exact excerpt hashes and retrieval
  times, plus findings that cite only recorded source ids;
- `prompts.json`: presentation treatment and exact instructions for `front`,
  `top`, `bottom`, `exploded`, and every stable component. Preserve the declared
  dependency order: front; top/bottom from front; exploded from all three;
  components from front only;
- `descriptor.json`: one distinct permitted image path for every overall and
  component role, with path-only leaves; and
- `derived_wish.json`: the original Wish words and context unchanged, plus the
  researched physical constraints that Make must obey.

Do not add source files, placeholder values, rendered images, provider ids, or
credentials. Reconcile component names across the Invented source, brief,
prompts, descriptor, and mechanism before finalizing. On a revision, use the
packet's exact standing sealed Concept and revision evidence; author a fresh
round tree rather than editing or reusing the old one.

## Complete authored-source schema

This section is the complete agent-facing shape for the five authored JSON
objects. It is the contract to use before calling the finalizer; do not infer
fields from finalizer errors. Every file is one strict UTF-8 JSON object no
larger than 2 MiB: no duplicate keys, non-finite numbers, links, special
files, or additional files at `concept_root`. All identifiers below match
`[a-z0-9][a-z0-9_-]{0,63}`. All text is non-empty and must not be a placeholder
such as `TBD`, `TODO`, `unknown`, `placeholder`, `n/a`, or `later`.

`brief.json` has this canonical skeleton. The Manager must replace every
angle-bracket value with the decided design content. `fit_target` is required
for this marked compound Concept capability.

```json
{
  "object": "<decided physical object>",
  "category": "<product category>",
  "envelope_mm": {
    "length_mm": 0.0,
    "width_mm": 0.0,
    "height_mm": 0.0
  },
  "wall_thickness_mm": 0.0,
  "print_stance": {
    "orientation": "<print orientation>",
    "supports_required": false,
    "support_notes": "<support decision and reason>"
  },
  "features": [
    {
      "id": "<feature-id>",
      "text": "<distinctive feature, not merely the Wish objective>"
    }
  ],
  "fit_target": {
    "target": "<interface or fit target>",
    "dimensions_mm": {
      "length_mm": 0.0,
      "width_mm": 0.0,
      "height_mm": 0.0
    },
    "clearance_mm": 0.0
  },
  "components": [
    {
      "key": "<stable-component-key>",
      "name": "<component name>",
      "purpose": "<why this part exists>",
      "form": "<specific physical form>",
      "dimensions_mm": {
        "length_mm": 0.0,
        "width_mm": 0.0,
        "height_mm": 0.0
      },
      "placement": "<where it sits in the object>",
      "interfaces": "<contacts, clearances, or attachments>"
    }
  ],
  "facts": [
    {
      "field": "object",
      "source_id": "<recorded-source-id>",
      "assumption_reason": null
    },
    {
      "field": "features.<feature-id>",
      "source_id": null,
      "assumption_reason": "<reasoned design decision>"
    },
    {
      "field": "components.<stable-component-key>",
      "source_id": "<recorded-source-id>",
      "assumption_reason": null
    }
  ]
}
```

Every dimension and `wall_thickness_mm` is a positive finite number;
`clearance_mm` is finite and zero or greater. `features` and `components` are
non-empty and their `id`/`key` values are unique. Each component object has
exactly the seven fields shown. `facts` must contain exactly one entry for
every required field: `object`, `category`, `envelope_mm`,
`wall_thickness_mm`, `print_stance`, `fit_target`, every
`features.<feature-id>`, and every `components.<stable-component-key>`. In
each fact, set exactly one of `source_id` and `assumption_reason` to non-empty
text; a source id must occur in `research.json`.

Field bounds are exact: `object` and `category` are at most 2,000 characters;
`print_stance.orientation` at most 1,000; `print_stance.support_notes` and
each feature `text` at most 2,000; component `name` at most 200; and component
`purpose`, `form`, `placement`, and `interfaces` at most 4,000. A fact's
`field` is one of the required field names listed above; its `source_id` is a
recorded identifier, while its decision `assumption_reason` need only be a
non-empty string within the file limit.

`research.json` has exactly these nested entry shapes:

```json
{
  "sources": [
    {
      "id": "<source-id>",
      "origin": "<source URL, citation, or other bounded origin>",
      "excerpt": "<the bounded supporting text>",
      "excerpt_sha256": "<sha256 of the canonical JSON string excerpt>",
      "retrieved_at": "<UTC ISO-8601 timestamp>"
    }
  ],
  "findings": [
    {
      "finding": "<bounded finding supported by the sources>",
      "source_ids": ["<source-id>"]
    }
  ]
}
```

Both arrays are non-empty. Source ids are unique; every finding names one or
more distinct source ids from `sources`. `excerpt_sha256` is the SHA-256 of
the UTF-8 canonical JSON encoding of the excerpt string: sorted keys,
compact separators, `ensure_ascii=false`, and no newline.

`origin` is at most 4,000 characters; `excerpt` and `finding` are at most
8,000. `retrieved_at` must be a valid UTC timestamp. A source `id` is the
same bounded identifier described above.

`prompts.json` has one presentation treatment and this exact dependency graph.
`front` has no references; `top` and `bottom` reference only `front`;
`exploded` references `front`, `top`, then `bottom`; each component references
only `front`. The `components` keys must equal the brief component keys, and
the exploded instruction must name every component's `name`.

```json
{
  "presentation": "<one consistent rendering treatment>",
  "front": {"instruction": "<front instruction>", "references": []},
  "top": {"instruction": "<top instruction>", "references": ["front"]},
  "bottom": {"instruction": "<bottom instruction>", "references": ["front"]},
  "exploded": {
    "instruction": "<exploded instruction naming every component>",
    "references": ["front", "top", "bottom"]
  },
  "components": {
    "<stable-component-key>": {
      "instruction": "<component-only instruction>",
      "references": ["front"]
    }
  }
}
```

Each role object has exactly `instruction` and `references`; instructions are
non-empty bounded text. `presentation` is at most 2,000 characters and every
role instruction is at most 8,000. `presentation` is required for this marked
protocol.

`descriptor.json` declares the pre-render image locations only. Its top-level
roles and component keys must exactly match `prompts.json` and `brief.json`.
Every leaf has exactly one `path`; paths are unique safe relative POSIX paths
under the Concept root and end in `.png`, `.jpg`, `.jpeg`, or `.webp`. Do not
put a `sha256` in this pre-render descriptor: the host adds it only when it
seals returned image bytes.

```json
{
  "front": {"path": "images/front.png"},
  "top": {"path": "images/top.png"},
  "bottom": {"path": "images/bottom.png"},
  "exploded": {"path": "images/exploded.png"},
  "components": {
    "<stable-component-key>": {
      "path": "images/components/<stable-component-key>.png"
    }
  }
}
```

`derived_wish.json` has exactly these eight fields. Copy `wish_sha256`,
`product_id`, `objective`, and `context` byte-for-value from the packet-bound
Wish; never summarize or rewrite them. `constraints` is a non-empty object of
the researched physical constraints Make must obey. Compute
`derived_wish_sha256` last as the SHA-256 of the canonical JSON object formed
by the first seven fields (exclude `derived_wish_sha256` itself), using sorted
keys, compact separators, UTF-8, `ensure_ascii=false`, finite JSON, and no
newline.

`product_id` is non-empty text of at most 256 characters; `objective` is
non-empty text of at most 50,000 characters. `context` and `constraints` must
be finite JSON objects; `constraints` cannot be empty.

```json
{
  "schema_version": 1,
  "kind": "autonomous-workshop.concept-derived-wish",
  "wish_sha256": "<packet Wish sha256>",
  "product_id": "<packet product id>",
  "objective": "<packet objective unchanged>",
  "context": {"<packet context key>": "<packet context value>"},
  "constraints": {"<constraint-name>": "<researched physical constraint>"},
  "derived_wish_sha256": "<computed canonical identity sha256>"
}
```

Invoke exactly one ready finalizer after both the four-field creative source
and five-file tree are complete:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json> \
  --concept-root <STAGE.json.inputs.concept_root>
```

The finalizer only validates, derives provenance, and preserves exact bytes.
It never researches, composes prompts, renders, reads credentials, judges
meaning, seals returned images, or advances the lifecycle. After it succeeds,
complete the same Invent Goal and return control. The host performs authorized
effects after the native process exits and may later resume this same session
at Make; do not invoke another finalizer for host-rendered bytes.
