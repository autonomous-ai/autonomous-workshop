# Bought Part price estimates, Vietnam retail, 2026-11-06

Every price here is an **estimate**. It sets `unit_price_cents` in
`src/workshop/wish/catalogues/bought-parts.json`. Nothing was ordered, and no
entry is confirmed by this note. Pack size and `source` (where the maker buys)
stay as they were.

- **Date checked:** 2026-11-06, for every listing below.
- **Sources:** Vietnamese shops only: thegioiic, icdayroi, banlinhkien, nshopvn,
  hshop, linhkienchatluong, Tiki, Lazada VN, Shopee VN (read through BigGo),
  Fahasa, Bách Hóa Xanh, and fastener dealers.
- **What a unit is:**
  - For pieces, the typical price of one piece when a small shop buys a small
    pack.
  - For consumables, one pack as bought: one roll, spool or box. This is
    because Release multiplies `unit_price_cents` by the count of bodies or
    lines.
- **Exchange rate:** 25,780 VND per USD. This is Vietcombank's USD sell rate,
  updated 16:45 on 2026-11-06, read on https://webgia.com/ty-gia/vietcombank/.
  Vietcombank's buy rates that day were 25,370 cash and 25,400 transfer. The
  rate on 2026-11-03 was 25,980.
- **Cents:** `ceil(VND / 25,780 × 100)`, with a minimum of 1 cent.
- **Confidence** is the researcher's judgement:
  - high: several matching listings agree.
  - medium: one close listing, or close proxies.
  - low: a proxy or inferred price only.

## Prices

| Entry | Unit | Est. VND | Cents | Listings (2026-11-06) | Confidence |
|---|---|---:|---:|---|---|
| battery-box-2aa-switch | piece | 9,000 | 35 | banlinhkien.com/hop-de-pin-2aa-co-nap-p6651524.html (12,000); icdayroi.com/de-2-pin-aa-co-nap-cong-tac (9,000); nshopvn.com/product/hop-de-2-pin-aa-co-nap-va-cong-tac/ (8,000) | high |
| led-3v-warm-white | piece | 3,500 | 14 | lammohinh.vn/product/den-led-soi-0603/ (32,000, pack unclear) | low |
| led-3v-cool-white | piece | 3,500 | 14 | same as warm white | low |
| steel-pin-1.5x29.5 | piece | 1,500 | 6 | tiki.vn/cuon-day-inox-304-phi-1-5-mm-…-p189070401.html (43,200 per 10 m coil); shopee.vn/product/1163178994/24336295482 (49,000 per 3 × 50 cm rods); nshopvn.com/product/truc-2mm-dai-80mm/ (2,000, proxy) | low: no ready-cut pin listed |
| spring-compression-6x0.5x20-stainless | piece | 3,000 | 12 | tbstap.com/san-pham/lo-xo-nen-phi-6-dai-20-soi-0-5mm-inox-304/ (3,800, exact spec); Shopee via BigGo 0.6 × 6 × 20 (28,000 per 10); shopee.vn/product/133819556/24751324418 (58,000 per 20) | medium |
| cork-disc-95x3 | piece | 10,000 | 39 | tiki.vn/mieng-lot-ly-hinh-tron-bang-go-ban-tu-nhien-p186584816.html (10,000, 90 × 3); tiki.vn p146781819 (20,000, wood) | medium-low |
| screw-m2x8-pan-self-tapping | piece | 190 | 1 | thegioiic.com/vit-dau-pan-pb-m2-x-8-mm (194); thegioiic.com/vit-pb-m2-x-8mm-304 (342, stainless) | medium |
| clear-jar-6x7 | piece | 4,000 | 16 | nothing near 6 × 7 mm; tiki.vn p152449157 (1 mL vial 11 × 22, no price) | low: size not found |
| foam-tape | roll, 24 mm × 5–6 m | 15,000 | 59 | tiki.vn/bang-keo-xop-2-mat-2-4cm-p20330908.html (15,000); lazada.vn …i2410814708.html (18,000); tiki BK7A (61,230 per 5 rolls) | medium-high |
| foam-dots | pack of 10 | 12,000 | 47 | tiki.vn/combo-10-mieng-dan-keo-2-mat-xop-sieu-dinh-p150783204.html | low-medium |
| glue | tube | 8,000 | 32 | fahasa.com/keo-502-ii.html (10,500); tiki Deli set of 3, p264016445 (19,000); tiki Thuận Phong p202641505 (about 10,000–12,000) | medium-high |
| tweezers | piece | 20,000 | 78 | thegioiic.com/vetus-st-15-nhip-gap-linh-kien-dau-cong-dai-115mm (14,820); nshopvn.com/product/nhip-cong-onlyou-esd-15/ (20,000); thegioiic.com/esd-249-… (27,360) | high |
| screwdriver | piece | 6,000 | 24 | lazada.vn/products/bo-10-bo-tua-vit-mini-…-i13403919221.html (59,000 per 10); thegioiic.com/l85-2-0-tua-vit-hinh-chu-thap-dai-85mm (2,280); hshop.vn/tua-vit-bake-ph1x100mm-wadfow-wsd2214-phillips-screwdriver (15,000, PH1, likely too large for M2) | medium |
| cell-aaa | cell | 17,000 | 66 | Bách Hóa Xanh Panasonic LR03T (34,000 per 2); Điện Máy Xanh (35,000 per 2); Thế Giới Di Động (32,000 per 2); Tiki Duracell (35,000 per 2) | high |
| contact-aaa-spring | piece | 1,000 | 4 | thegioiic hop-pin-aa?prid=2063 (570–912 per set, AA); tiki.vn/de-tiep-dien-de-lo-xo-pin-…-p200962855.html (15,000 per pack) | low |
| contact-aaa-plate | piece | 1,000 | 4 | same as the spring | low |
| contact-aaa-bridge | piece | 2,000 | 8 | no Vietnamese listing; inferred from the spring and plate | low |
| microswitch-mini-lever | piece | 4,000 | 16 | thegioiic KW12-C (3,420); icdayroi.com/cong-tac-hanh-trinh-kw12-3-chan-cong (6,000); nshopvn.com/product/cong-tac-hanh-trinh-kw12/ (3,000–5,000); linhkienchatluong.vn/cong-tac-hanh-trinh_s858.aspx (6,000) | high |
| led-5mm-amber-diffused | piece | 300 | 2 | thegioiic.com/led-vang-5mm-duc-chan-dai (285); icdayroi.com/led-duc-mau-vang-5mm (3,000 per 10) | medium |
| resistor-75r | piece | 100 | 1 | icdayroi.com/dien-tro-75-ohm-1-4w-1-goi-50-con (7,000; pack 50 or 100); banlinhkien.com/tro-vach-14w-5-75r-50c-p6650248.html (6,000 per 50) | medium-high |
| wire-28awg | metre | 2,500 | 10 | linhkienviet.vn/hop-5-cuon-day-dien-ul1007-… (189,900 per 100 m, UL1007); vietnic.vn/day-dien-doi-do-den-2p-22awg-2x0-17-1m (3,000 per m); lazada.vn …i13331802593… (232,000 per 10 m, silicone) | medium |
| screw-m2x6-pan | piece | 170 | 1 | thegioiic.com/vit-pm-m2-x-6mm (180; 169 at 100); thegioiic.com/vit-pm-m2-x-6mm-304 (303); nshopvn.com/product/oc-vit-dau-tron-ma-ni-ken/ (5,000 per 50) | high |
| heat-shrink | box, about 530 pcs | 65,000 | 253 | banlinhkien.com/hop-530-ong-gen-co-nhiet-cach-dien-p21058011.html (65,000); banlinhkien.com/hop-580-ong-gen-co-nhiet-p38419303.html (115,000); icdayroi.com/combo-ong-co-nhiet-328-chiec (30,000 on sale, 50,000 list) | high |
| solder | 50 g spool | 105,000 | 408 | banlinhkien.com/thiec-han-sn63-0.8mm-50g-ssn630850-p6653099.html (110,000); icdayroi.com/thiec-han-mechanic-6337-0-3mm-55g (98,000); hshop.vn/thiec-han-sieu-bong-nhe-lua-hsolder-100g-sn63-pb37-solder-wire (165,000 per 100 g) | high |
| soldering-iron | piece, 60 W adjustable | 190,000 | 738 | icdayroi.com/mo-han-chi-no-907-60w (190,000); icdayroi.com/mo-han-chi-dieu-chinh-nhiet-do-co-lcd-hien-thi-60w (195,000); banlinhkien.com/tay-han-no.90760w-220v-p6652324.html (240,000); hshop.vn/mo-han-dieu-chinh-nhiet-do-70w-total-tet01606 (175,000) | high |
| usb-c-receptacle-power | piece | 1,500 | 6 | thegioiic.com/products/cong-usb-cai-3-0-type-c-6-chan-thang-dan-smd (1,710); linhkienchatluong.vn/…cong-usb-type-c-31-chan-dan-6p-smd-2-chot-cam-thang_sp715_ct15000.aspx (1,250–1,500) | medium-high |
| led-2835-warm-2200k | piece | 400 | 2 | thegioiic "LED Trắng Ấm 2835" (399; thegioiic.com/tim-kiem?q=led%202835) | medium; 2200 K not confirmed |
| led-2835-pink | piece | 500 | 2 | no single LED; linhkienlammusic pink strip (43,000 per 5 m); banlinhkien.com/led-dan-pc535353.html (3528 colours, 2,000–5,000 per 5) | low: inferred |
| led-2835-cyan | piece | 500 | 2 | no Vietnamese listing; inferred like pink. The catalogue's LCSC source quotes USD 0.095 at 200+ for the specified Cree part, so this estimate is likely low for that exact part | very low |
| resistor-150r | piece | 60 | 1 | icdayroi.com/dien-tro-150-ohm-0805-1-goi-50-con (6,000 per 100); banlinhkien.com/tro-0805-5-150r-5000-chiec-p22080222.html (250,000 per 5,000) | high |
| resistor-470r | piece | 60 | 1 | icdayroi.com/dien-tro-470-ohm-0805-1-goi-50-con (6,000 per 100); banlinhkien 0805 category, /tro-0805-1-pc535288.html (3,500 per 50) | high |
| resistor-110r | piece | 60 | 1 | no 0805 110R listing; flat 0805 pricing above; banlinhkien.com/tro-vach-14w-5-110r-50c-p31766390.html (axial, 6,000 per 50) | medium |
| test-tube-pp-25x150 | piece | 12,000 | 47 | no Vietnamese PP 25 × 150 listing; labvietchem glass 25 × 150 ("Liên hệ"); Lazada Mida PP 12 × 75, i791774138 | very low. The supplier source already recorded (TWD Scientific, US) is about USD 0.70 each |
| threaded-rod-m6x250 (new) | 250 mm piece | 2,500 | 10 | bulonganphong.vn/bang-gia-ty-ren-thanh-ren/ (3,150 per m, electro-zinc, wholesale); phukienhoangvy.com/sp/thanh-ty-ren-m6-kem/ (4,500–5,200 per m); thepbaotin.com/ty-ren/ (7,500–8,500 per m). Estimate: about 10,000 per m at small retail, a quarter bar | medium |
| nut-m6-iso4032 (new) | piece | 300 | 2 | thegioiic.com/dai-oc-thep-m6 (627); thegioiic.com/m6-dai-oc-thep-carbon-den (285); congnghiep21 DIN 934 zinc (250) | high |
| washer-m16-iso7093-50x3 (new) | piece | 4,000 | 16 | b2bmart.vn/long-den-phang-thep-ma-den-m16-50x4-0-s0-pd8550.html (4,400, 50 × 4, minimum 50); mecsu.vn/chi-tiet/long-den-phang-thep-ma-den-m16-50x40.q1J2 (3,731, 50 × 4) | medium price, no 50 × 3 listing |
| washer-m12-iso7089 (new) | piece | 1,300 | 6 | anhduongvina.com/san-pham/long-den-phang-thep-ma-kem-m12-din-125/ (2,300); mecsu.vn/chi-tiet/long-den-phang-thep-ma-kem-m12-24x25.ZJQd (364); thegioiic.com/long-den-kin-m12-x-24mm-day-2-2mm-304 (2,736, stainless) | low-medium |
| switch-push-latching-8x8 (new) | piece | 2,500 | 10 | dientunguyenhien.vn/show/626 (2,800, 8 × 8 self-locking, 6-pin); robocon.vn/detail/sw9-nut-nhan-6-chan-8x8mm.html (2,500 for 1–19); banlinhkien.com/nut-nhan-6-chan-8x8mm-nhan-giu-5-chiec-p23175903.html (8,000 per 5); nshopvn.com/product/nut-nhan-6-chan-8x8 (1,500, out of stock); caka.vn/nut-nhan-6-chan-8x8 (1,000) | medium-high: 8 × 8 listings; no Vietnamese 8.5 × 8.5 listing found |

## Caveats

- **Shopee and Lazada:** these pages render prices with JavaScript, so their
  prices came from BigGo or search snippets. The Mecsu pages returned 403, so
  their prices are from snippets too.
- **No close Vietnamese listing was found for:** clear-jar-6x7, contact-aaa-bridge,
  led-2835-pink, led-2835-cyan, test-tube-pp-25x150, steel-pin-1.5x29.5, and
  the exact 50 × 3 M16 washer. Re-price these once the owner chooses a
  supplier.
- **Rounding:** sub-cent parts (screws, resistors) are rounded up to 1 cent.
- **Confirming:** an estimate does not confirm an entry. `confirmed`, `pack`
  and `source` change only when the owner supplies them.
