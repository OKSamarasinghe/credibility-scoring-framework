import re

path = "docs/methodology.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

orig = text

# 1. Status paragraph
old = """**Status, 2026-10-08:** data audit complete and corrected twice; Stage 1 complete and
tested; **Stage 2 complete — 200/200 posting manual audit coded by hand (commit
`57da423`), results below**; **Stage 3 complete — group-aware 70/15/15 split run and
verified (commit `9a5379b`), results below**; Stage 8 skeleton (API routing/schema, no
real pipeline yet) complete and tested. Stages 4–7, 9 not started."""
new = """**Status, 2026-10-08:** data audit complete and corrected twice; Stage 1 complete and
tested; **Stage 2 complete — 200/200 posting manual audit coded by hand (commit
`57da423`), results below**; **Stage 3 complete — group-aware 70/15/15 split run and
verified (commit `9a5379b`), results below**; **Stage 4 complete — E1–E4 extraction built
and run on the full corpus (n=17,880), 33/33 new tests passing, results below**; Stage 8
skeleton (API routing/schema, no real pipeline yet) complete and tested. Stages 5–7, 9 not
started."""
assert old in text, "status paragraph not found"
text = text.replace(old, new)

# 2. Implementation stages table row
old = "| 4 | Multi-signal evidence extraction | O1, O3 | ⬜ Not started |"
new = "| 4 | Multi-signal evidence extraction | O1, O3 | ✅ Complete, 2026-10-08 — E1-E4 built and run on full corpus; 4 precision bugs found & fixed; see Stage 4 extraction results below |"
assert old in text
text = text.replace(old, new)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("part 1 OK, net change:", len(text) - len(orig))
