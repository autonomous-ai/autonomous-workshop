"""Postcondition checks for the existing Shop Door product-page pipeline.

Alice does not generate merchandising content here. The out-of-band pipeline
does. Alice waits for the public design record and verifies that the finished
page contract is complete before marking a candidate published.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


ALICE_PRODUCT_DESCRIPTION_SUFFIX = "By Alice."


def has_exact_alice_product_description_suffix(description: Any) -> bool:
    """Return whether a product description has Alice's exact final attribution."""

    return (
        isinstance(description, str)
        and description.rstrip() == description
        and not description.endswith(
            f"Note: {ALICE_PRODUCT_DESCRIPTION_SUFFIX}"
        )
        and description.endswith(ALICE_PRODUCT_DESCRIPTION_SUFFIX)
    )


@dataclass(frozen=True, slots=True)
class PageVerification:
    complete: bool
    page_url: str
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    image_count: int
    video_count: int
    story_count: int


def verify_shop_door_page(
    design: Mapping[str, Any],
    *,
    public_base_url: str = "https://www.autonomous.ai/factory/product",
    expected_price_cents: int | None = None,
    expected_currency: str | None = None,
) -> PageVerification:
    failures: list[str] = []
    warnings: list[str] = []
    slug = design.get("slug")
    if not isinstance(slug, str) or not slug:
        failures.append("slug_missing")
        slug = "missing"
    page_url = f"{public_base_url.rstrip('/')}/{slug}"
    if design.get("status") != "public":
        failures.append("design_not_public")
    for key in ("id", "title", "description", "project_url"):
        if not design.get(key):
            failures.append(f"{key}_missing")
    description = design.get("description")
    if description and not has_exact_alice_product_description_suffix(description):
        failures.append("description_attribution_invalid")
    category = design.get("category")
    if not isinstance(category, Mapping) or not category.get("slug"):
        # The current Vibe pipeline can produce a complete customer-facing page
        # before catalog taxonomy is attached (Arrows is the live precedent).
        # Keep this visible for merchandising/SEO without deadlocking page_ready.
        warnings.append("category_missing")

    media: list[str] = []
    primary = design.get("primary_thumbnail_url")
    if isinstance(primary, str) and primary:
        media.append(primary)
    thumbnails = design.get("thumbnail_urls")
    if isinstance(thumbnails, list):
        media.extend(item for item in thumbnails if isinstance(item, str) and item)
    if not media:
        failures.append("hero_media_missing")

    use_case = design.get("use_case")
    if not isinstance(use_case, Mapping):
        failures.append("use_case_missing")
    else:
        for key in ("label", "body", "image"):
            if not use_case.get(key):
                failures.append(f"use_case_{key}_missing")
        if isinstance(use_case.get("image"), str):
            media.append(use_case["image"])

    story = design.get("story_blocks")
    story_count = len(story) if isinstance(story, list) else 0
    if story_count < 3:
        failures.append("story_blocks_below_three")
    if isinstance(story, list):
        for index, block in enumerate(story):
            if not isinstance(block, Mapping):
                failures.append(f"story_{index}_invalid")
                continue
            if not block.get("lead") or not block.get("body"):
                failures.append(f"story_{index}_copy_missing")
            block_media: list[str] = []
            hero = block.get("hero_image")
            if isinstance(hero, str) and hero:
                block_media.append(hero)
            pair = block.get("pair_images")
            if isinstance(pair, list):
                block_media.extend(item for item in pair if isinstance(item, str) and item)
            if not block_media:
                failures.append(f"story_{index}_media_missing")
            media.extend(block_media)

    specs = design.get("print_specs")
    if not isinstance(specs, Mapping):
        failures.append("print_specs_missing")
    else:
        for key in ("dimensions_mm", "weight_g", "print_time_minutes", "part_count", "materials"):
            if specs.get(key) in (None, [], {}):
                failures.append(f"print_specs_{key}_missing")
    parts = design.get("assembly_parts")
    if not isinstance(parts, list) or not parts:
        failures.append("assembly_parts_missing")

    listing = design.get("listing")
    if not isinstance(listing, Mapping) or listing.get("active") is not True:
        failures.append("active_listing_missing")
    else:
        for key in ("sku", "price_cents", "currency", "ships_within_days"):
            if listing.get(key) is None:
                failures.append(f"listing_{key}_missing")
        if expected_price_cents is not None and listing.get("price_cents") != expected_price_cents:
            failures.append("listing_price_mismatch")
        if expected_currency is not None and listing.get("currency") != expected_currency:
            failures.append("listing_currency_mismatch")

    deduplicated = tuple(dict.fromkeys(media))
    video_count = sum(
        1
        for url in deduplicated
        if url.lower().split("?", 1)[0].endswith((".mp4", ".webm", ".mov"))
    )
    image_count = len(deduplicated) - video_count
    if image_count + video_count < 5:
        failures.append("visual_assets_below_five")
    return PageVerification(
        complete=not failures,
        page_url=page_url,
        failures=tuple(failures),
        warnings=tuple(warnings),
        image_count=image_count,
        video_count=video_count,
        story_count=story_count,
    )


# Read-only import compatibility for integrations built before Workshop 0.3.
verify_factory_product_page = verify_shop_door_page
