#!/bin/bash
# Re-download the official Rolife 2026 manuals into sources/manuals-2026/.
# The PDFs are Robotime's, publicly linked from rolifeonline.com; they are kept out of git.
set -e
cd "$(dirname "$0")"; mkdir -p sources/manuals-2026; cd sources/manuals-2026
B=https://cdn-files.myshopline.com/file/store/1649394707320
for f in \
  DH201-Rolife-Leafree-Cafe-DIY-Miniature-House-Assembly-Instruction-EN.pdf \
  DH102-Rolife-Oxygen-Oasis-DIY-Miniature-House-Assembly-Instruction-EN.pdf \
  DH101-Rolife-Sunlit-Farmhouse-Kitchen-DIY-Miniature-House-Assembly-Instruction-EN.pdf \
  DG186-Rolife-Haunted-Candy-House-DIY-Miniature-House-Assembly-Instruction-EN.pdf \
  DG185-Rolife-Fluffy-Friends-Store-DIY-Miniature-House-Assembly-Instruction-EN.pdf \
  DG184.pdf \
  TGB19-Wisdom-Stationery-Shop-Assembly-Instruction-EN.pdf \
  TGB18-Rolife-Sunset-Isle-Assembly-Instruction-EN.pdf \
  TGE05-Rolife-Nostalgic-Corner-Shop-DIY-Book-Nook-Assembly-Instruction-EN.pdf; do
  [ -s "$f" ] || curl -fsSL -o "$f" "$B/$f"
done
ls -la
