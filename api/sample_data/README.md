# Bundled demo case

`spleen_10/` is one abdominal CT from the public **Medical Segmentation Decathlon —
Task09 Spleen** dataset ([medicaldecathlon.com](http://medicaldecathlon.com),
CC-BY-SA 4.0), plus the organ masks OrganAI displays (produced by TotalSegmentator).

It powers the **Sample CT** tab so the app has an instant, no-upload demo on a fresh
deploy. Only the ~10 displayed-organ masks are included to keep the bundle small.

To use your own demo instead, replace these files (or add entries to
`api/samples.json`) and point the manifest at them.
