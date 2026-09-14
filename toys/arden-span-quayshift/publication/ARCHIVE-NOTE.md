# GitHub snapshot provenance

This snapshot was materialized after the public Factory release on
2026-09-14. GitHub publication was not enabled for that run, so the original
materialization did not commit or push it. The inventor and both published
Arden toys were subsequently added to the repository together.

`PUBLICATION.json` preserves the authenticated observation from
2026-09-14T01:46:39.378640+00:00. A new unauthenticated API/CDN check during
GitHub preparation returned HTTP 403; that attempt does not refresh the
recorded publication status or establish the site's current version.

The Python sources, STEP files, challenges and product views retain their
original bytes. `SANITIZATION.json` records the public projection of host
paths in CAD verification and in the generated `assembled.step.json` index.
The index's external Python dependency paths now use
`<PYTHON_SITE_PACKAGES>`; its original closure hash is historical provenance,
not a promise that the redacted dependency list reproduces that hash.
Sealed Made/Release hashes continue to identify the original artifacts.
`MANIFEST.json` identifies the sanitized files actually stored here.

The standalone source entry is `../make/source/cad/quayshift.step.py`;
`quayshift_lib.py` and `layouts.json` are beside it. The final assembly is
`../make/models/assembled.step`, with individual STEP parts under
`../make/models/cad/`. Product rules and three delivered challenges are under
`../make/product/`. A later Wish is a new generation, not an exact replay.

No physical print or human playtest is established by this archive.
