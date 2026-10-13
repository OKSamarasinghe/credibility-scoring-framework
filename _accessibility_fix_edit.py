import io

path = "frontend/index.html"
with io.open(path, encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)
orig_script_marker = content.count("const form = document.getElementById")

# ---------- 0. small CSS addition for the new secondary technical-detail line ----------
css_block = '''
  /* ---------- plain-language-first trust figures -- added 2026-10-13 ---------- */
  .trust-card .trust-detail { margin-top: 8px; font-size: 0.74rem; color: var(--muted); }
'''
old_style_anchor = "</style>\n</head>"
assert content.count(old_style_anchor) == 1
content = content.replace(old_style_anchor, css_block + old_style_anchor, 1)

# ---------- 1. Calibration badge: plain language first, technical detail second ----------
old_badge_1 = '          <span class="trust-figure">Measured calibration error (ECE): 0.0076 on held-out test data</span>'
new_badge_1 = ('          <span class="trust-figure">Checked against real postings the model never trained on — and it held up.</span>\n'
               '          <p class="trust-detail">Technical detail: calibration error (ECE) of 0.0076, measured once on a held-out test set.</p>')
assert content.count(old_badge_1) == 1, "badge 1 not found"
content = content.replace(old_badge_1, new_badge_1, 1)

# ---------- 2. SHAP/explanation badge: plain language first, technical detail second ----------
old_badge_2 = '          <span class="trust-figure">Explanations tested, not just shown: fired consistency flags appear in their own top reasons 100% of the time (14/14 tested)</span>'
new_badge_2 = ('          <span class="trust-figure">Every time the system flagged a contradiction, the explanation named it — not just sometimes, every single case checked.</span>\n'
               '          <p class="trust-detail">Technical detail: 14 out of 14 fired consistency-rule cases appeared in their own top reasons.</p>')
assert content.count(old_badge_2) == 1, "badge 2 not found"
content = content.replace(old_badge_2, new_badge_2, 1)

# ---------- 3. Example card 2 (Stripe): clarify the counter-intuitive "missing field raised the score" line ----------
old_caption = '          <p class="example-source">Source: Stage 8b demonstration, <code>reports/stage8b_demonstration.json</code> -- the system\'s unedited output. Despite missing structured fields, the language model\'s reading of the detailed, genuine posting text is what drove this score -- the reason text and structured evidence are combined, not used alone.</p>'
new_caption = ('          <p class="example-source">Source: Stage 8b demonstration, <code>reports/stage8b_demonstration.json</code> -- the system\'s unedited output. One line above may look backwards at first — "missing field... raised the score" — but that\'s not an error. The system weighs a posting as a whole, not as a checklist, so a single missing field is never automatically held against (or for) a posting on its own. Here, the detailed, genuine Stripe text is what actually earned the high score; the missing fields barely mattered once the real content was read.</p>')
assert content.count(old_caption) == 1, "example caption not found"
content = content.replace(old_caption, new_caption, 1)

new_script_marker = content.count("const form = document.getElementById")
assert new_script_marker == orig_script_marker == 1, "script block marker changed -- aborting"

with io.open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("OK. bytes before:", orig_len, "after:", len(content), "delta:", len(content) - orig_len)
