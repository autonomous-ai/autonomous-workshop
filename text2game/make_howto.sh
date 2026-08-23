#!/bin/bash
# Join the per-beat clips into one how-to, with the rule burnt onto each beat.
#
# The video model returns ~12s from one still and one prompt. Three rules beats
# in 12s is at its documented ceiling and the first coach-party take proved it:
# it spent the clip on a camera move and taught nothing. One action per clip,
# then joined here, gives each beat the whole 12s.
#
# The caption is not decoration. This model pushes in no matter how hard the
# prompt locks the camera, so a viewer sees a close-up of ONE action with no
# idea which rule it is. The text is what makes the clip legible.
#
#     ./make_howto.sh out/<slug> <out.mp4> "cap1" "cap2" "cap3" ...
set -euo pipefail
D="$1"; OUT="$2"; shift 2
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
W=1280; H=720
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
i=0; list="$TMP/list.txt"; : > "$list"
for cap in "$@"; do
  i=$((i+1))
  src="$D/howto_b$i.mp4"
  [ -f "$src" ] || { echo "missing $src"; exit 1; }
  esc=$(printf '%s' "$cap" | sed "s/'/\\\\\\\\'/g; s/:/\\\\:/g; s/,/\\\\,/g")
  # Shrink to fit rather than run off the edge. The first join clipped a
  # 79-character line to "three h" at size 30, which is worse than small text:
  # the caption is the only thing telling the viewer WHICH RULE they are
  # watching. DejaVu Sans Bold averages ~0.6em per glyph.
  n=${#cap}
  fs=$(awk -v n="$n" 'BEGIN{f=int((W-2*M)/(0.6*n)); if(f>30)f=30; if(f<16)f=16; print f}' W=$W M=44)
  ffmpeg -v error -i "$src" \
    -vf "scale=$W:$H:force_original_aspect_ratio=decrease,pad=$W:$H:(ow-iw)/2:(oh-ih)/2:color=0x111417,\
drawbox=x=0:y=ih-96:w=iw:h=96:color=0x111417@0.82:t=fill,\
drawtext=fontfile=$FONT:text='$esc':fontcolor=0xF2EFE6:fontsize=$fs:x=(w-tw)/2:y=h-58-th/2:box=0" \
    -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 128k -ar 44100 \
    "$TMP/p$i.mp4"
  echo "file '$TMP/p$i.mp4'" >> "$list"
done
ffmpeg -v error -f concat -safe 0 -i "$list" -c copy "$OUT"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
echo "  $OUT  ${dur}s  $(du -k "$OUT" | cut -f1)KB"
