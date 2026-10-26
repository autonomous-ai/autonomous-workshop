# How commercial book nook kits are made

Research for designing printed book nooks as assembly kits in the style of Robotime's Rolife line. Gathered 2026-10-22 for the Night Charms Hall nook; meant for every later book nook.

## Files

| File | What it covers |
|---|---|
| [rolife-2026-book-nooks.md](rolife-2026-book-nooks.md) | Two 2026 book nooks, every manual page read: TGB18 Sunset Isle, TGE05 Nostalgic Corner Shop. Shell, faked depth, lighting, glue-free assembly. |
| [rolife-2026-houses.md](rolife-2026-houses.md) | Four 2026 kits: DH201 Leafree Café, DH102 Oxygen Oasis, DG186 Haunted Candy House, TGB19 Wisdom Stationery Shop. Materials, books, props, hinge, manual layout. |
| [rolife-dh103-pagestory.md](rolife-dh103-pagestory.md) | DH103 Pagestory Books (08/2026), the reference the owner chose. Its manual is not published; facts come from community reviews. |
| [rolife-assembly-trees.md](rolife-assembly-trees.md) | How six 2026 manuals structure assembly: step trees, wiring, access order, what paper lands on, tools and spares (for ADR 0092). |
| [fetch-sources.sh](fetch-sources.sh) | Re-downloads the nine 2026 manuals into `sources/manuals-2026/`. |

`sources/` holds the PDFs, the rendered page tiles, the product images and the review photos. They are Robotime's and reviewers' material, about 315 MB, and are kept out of git (listed in `.git/info/exclude`). On this machine they sit beside these notes; elsewhere, run `fetch-sources.sh`.

## Where the manuals come from

- Rolife's manual pages, one per model: `https://www.rolifeonline.com/blogs/assembly-instructions/<model>` (for example `dh201`). The page asks for an email before the download; the PDF link is in the page as `data-download-url`, on `cdn-files.myshopline.com`.
- Older manuals (2022–2025): https://www.robotimeonline.com/pages/assembly-guide.
- Product listing dates: `https://www.robotimeonline.com/products/<handle>.json` (`created_at`). Listings dated 2024-08-15 date the store migration, not the launch.
- Each PDF page is one very tall strip of many manual pages; render and slice it to read (the analyses used PyMuPDF at about 100 dpi).

## What carries over to a printed kit

1. Colour belongs to the material, never paint. Rolife prints its boards at the factory; a printed kit prints each part in one filament colour and moves everything multi-coloured to printed paper or stickers.
2. Books are never assembled one by one:
   - no printed strip of shelf spines was found in the 2026 manuals; TGB19 H24/H25 and S22/S23, once read as spine rows, are printed lids of colour-pencil and pen boxes on a sloped display (TGB19-13, -14; corrected 2026-10-26);
   - a loose or stacked book is a plain block wrapped in a printed cover (TGB19 Y-blocks with V-covers, TGB18 B16 + M7);
   - an open book is an accordion-folded paper strip on a cover board (TGE05 M24).
3. Pictures, posters, notices, labels, stone and floor textures, and the sky behind windows are printed paper; windows are clear film.
4. Small bought parts are used where printing would be crude: clear jars, beads, wire, florist wire with paper leaves.
5. A working hinge is a wire pin through a tube on the door edge (DH201 T27 + T57).
6. Book nooks press-fit with tabs and foam-tape pads, no glue (TGB18, TGE05); the house kits glue every joint.
7. Lighting is a 2×AAA touch-switch box or a USB-C board hidden in the base or behind; wires run in grooves or clips; the manual starts with a light test.
8. Manual: one section per prop or furniture item with a three-column material list (rigid parts / paper and stickers / other parts), props first, then shell, lighting, front and roof. Part IDs are sheet letter plus number, letters grouped by material, bagged by build stage.

## Release years (for weighing the older manuals)

| Model | Launched | Evidence |
|---|---|---|
| TGB03 Magic House | about 2022–2023 | eBay listing; current PDF is an 11/2025 reprint |
| DG155 Kiki's Magic Emporium | about 2023 | PDF created 07/2023 |
| DG164 Corner Bookstore | about early 2025 | PDF created 03/2025 |
| DW004 Fascinating Book Store | about 2025 | PDF created 06/2025; a plastic kit |
| TGB18, TGB19, TGE05, DH101, DH102, DH201, DG184–186 | 05–09/2026 | listing dates and PDF creation dates |
| DH103 Pagestory Books | 08/2026 | listed 2026-08-26 |

The analyses use only the 2026 manuals; `sources/manuals-2022-2025/` is kept for comparison.
