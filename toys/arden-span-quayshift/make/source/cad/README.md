# QUAYSHIFT CAD

Parametric millimetre sources: quayshift_lib.py contains dimensions and part builders; quayshift.step.py assembles the detour layout from layouts.json. part_*.step.py return each single part in its manufacturing orientation. Arches rest on their rear faces for printing; all other parts use their base. Colors are authored per leaf in sRGB. The board datum is its lower corner; architecture local origins are cell-reservation corners. Source transforms normalize quarter-turn footprints then translate to the board grid and floor datum.

Bed assumption: --bed 220x220x220. Printing status is established only by the final pipeline report. No physical print or human play session has occurred.

Gameplay, inventory and challenge assets are in the parent directory. The reference collage is qualitative inspiration with a clipped hero and unverified module inventory. It is not a complete whole-object silhouette suitable for numerical replica acceptance. Dimensions and final placements follow the original textual construction grammar.
