import io, sys

path = "frontend/index.html"
with io.open(path, encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)
orig_script_marker = content.count("const form = document.getElementById")

# ---------- 1. CSS insertion (before </style>) ----------
css_block = '''
  /* ---------- trust (calibration + SHAP explanation) -- added 2026-10-13 ---------- */
  .trust-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media (max-width: 760px) { .trust-grid { grid-template-columns: 1fr; } }
  .trust-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
    padding: 26px; box-shadow: var(--shadow-soft);
  }
  .trust-card .trust-icon {
    width: 38px; height: 38px; border-radius: 10px; background: var(--brand-light); color: var(--brand-dark);
    display: flex; align-items: center; justify-content: center; margin-bottom: 14px;
  }
  .trust-card .trust-icon svg { width: 20px; height: 20px; }
  .trust-card h3 { font-size: 1.02rem; margin: 0 0 10px; }
  .trust-card p { color: var(--muted); font-size: 0.9rem; margin: 0; }
  .trust-card .trust-figure {
    display: inline-block; margin-top: 12px; font-size: 0.78rem; font-weight: 700;
    color: var(--brand-dark); background: var(--brand-light); padding: 4px 10px; border-radius: 999px;
  }

  /* ---------- example (real Stage 8b demonstration output) -- added 2026-10-13 ---------- */
  .example-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media (max-width: 760px) { .example-grid { grid-template-columns: 1fr; } }
  .example-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
    padding: 24px; box-shadow: var(--shadow-soft);
  }
  .example-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 6px; }
  .example-score { font-size: 1.7rem; font-weight: 800; }
  .example-label { font-size: 0.82rem; color: var(--muted); margin: 0 0 14px; }
  .example-card ul { margin: 0; padding-left: 0; list-style: none; }
  .example-card li {
    position: relative; padding-left: 20px; margin-bottom: 8px; font-size: 0.85rem; color: var(--text);
  }
  .example-card li::before {
    content: ""; position: absolute; left: 0; top: 7px; width: 6px; height: 6px;
    border-radius: 50%; background: var(--muted);
  }
  .example-source {
    margin: 14px 0 0; font-size: 0.76rem; color: var(--muted); font-style: italic;
    padding-top: 12px; border-top: 1px dashed var(--border);
  }
'''

old_style_anchor = "</style>\n</head>"
new_style_anchor = css_block + "</style>\n</head>"
assert content.count(old_style_anchor) == 1
content = content.replace(old_style_anchor, new_style_anchor, 1)

# ---------- 2. Nav link insertion ----------
old_nav = '<a href="#evidence">Evidence model</a>'
new_nav = '<a href="#evidence">Evidence model</a>\n      <a href="#trust">Why trust it</a>'
assert content.count(old_nav) == 1
content = content.replace(old_nav, new_nav, 1)

# ---------- 3. New sections (trust + example), inserted between #evidence and about-band ----------
new_sections = '''  <section class="section" id="trust" style="padding-top:0;">
    <div class="container">
      <div class="section-head">
        <h2>Why the score isn't a black box</h2>
        <p>Two things keep this from being "trust us" -- a measured calibration, and explanations computed fresh for every posting.</p>
      </div>
      <div class="trust-grid">
        <div class="trust-card">
          <span class="trust-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
          </span>
          <h3>A calibrated score, not a made-up number</h3>
          <p>The model's raw prediction is passed through a calibration step before becoming your 0-100 score, so a posting scored around 70 really does behave, on average, like a posting that turns out legitimate roughly 70% of the time -- checked directly against real postings the model never trained on, not just assumed.</p>
          <span class="trust-figure">Measured calibration error (ECE): 0.0076 on held-out test data</span>
        </div>
        <div class="trust-card">
          <span class="trust-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M7 19V9M12 19V5M17 19v7"/></svg>
          </span>
          <h3>Reasons computed fresh for every posting</h3>
          <p>The reasons under "All observations" aren't a fixed checklist -- they're calculated individually for each posting using a technique called SHAP, which measures exactly how much each piece of evidence pushed that specific score up or down. That's why two similar-looking postings can get different reasons: the explanation reflects what actually mattered this time, not a generic rule applied to everyone.</p>
          <span class="trust-figure">Explanations tested, not just shown: fired consistency flags appear in their own top reasons 100% of the time (14/14 tested)</span>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="example" style="padding-top:0;">
    <div class="container">
      <div class="section-head">
        <h2>See it in action</h2>
        <p>Two real results from testing the system against real postings -- not illustrations, the system's actual output.</p>
      </div>
      <div class="example-grid">
        <div class="example-card">
          <div class="example-head">
            <span class="example-score" style="color:var(--high)">7 / 100</span>
            <span class="risk-chip band-High-chip"><span class="dot"></span>High risk</span>
          </div>
          <p class="example-label">A real scam report (consumer-reported employment scam)</p>
          <ul>
            <li>An employer profile was missing, which lowered the score.</li>
            <li>The posting's location (city) was NOT specified at this level, which lowered the score.</li>
            <li>Recommended check: "No direct contact channel was detected in the text -- confirm how you're expected to apply or follow up."</li>
          </ul>
          <p class="example-source">Source: Stage 8b demonstration, <code>reports/stage8b_demonstration.json</code> -- the system's unedited output.</p>
        </div>
        <div class="example-card">
          <div class="example-head">
            <span class="example-score" style="color:var(--low)">100 / 100</span>
            <span class="risk-chip band-Low-chip"><span class="dot"></span>Low risk</span>
          </div>
          <p class="example-label">A real company careers-page posting (Stripe)</p>
          <ul>
            <li>The posting's location (region) was specified at this level, which raised the score.</li>
            <li>An employer profile was missing, which lowered the score.</li>
            <li>The 'industry' field was missing, which raised the score.</li>
          </ul>
          <p class="example-source">Source: Stage 8b demonstration, <code>reports/stage8b_demonstration.json</code> -- the system's unedited output. Despite missing structured fields, the language model's reading of the detailed, genuine posting text is what drove this score -- the reason text and structured evidence are combined, not used alone.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="about-band">'''

old_section_anchor = '</section>\n\n  <section class="about-band">'
assert content.count(old_section_anchor) == 1
content = content.replace(old_section_anchor, "</section>\n\n" + new_sections, 1)

new_script_marker = content.count("const form = document.getElementById")
assert new_script_marker == orig_script_marker == 1, "script block marker count changed -- aborting"

with io.open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("OK. bytes before:", orig_len, "after:", len(content), "delta:", len(content) - orig_len)
