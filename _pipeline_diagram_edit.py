import io

path = "frontend/index.html"
with io.open(path, encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)
orig_script_marker = content.count("const form = document.getElementById")

# ---------- CSS addition for the diagram ----------
css_block = '''
  /* ---------- pipeline diagram (visual, replaces plain-text step summary) -- added 2026-10-13 ---------- */
  .pipeline-diagram-wrap { max-width: 960px; margin: 0 auto 8px; }
  .pipeline-diagram-wrap svg { width: 100%; height: auto; display: block; }
  .pipeline-caption { text-align: center; color: var(--muted); font-size: 0.84rem; margin: 10px 0 40px; }
'''
old_style_anchor = "</style>\n</head>"
new_style_anchor = css_block + "</style>\n</head>"
assert content.count(old_style_anchor) == 1
content = content.replace(old_style_anchor, new_style_anchor, 1)

# ---------- SVG diagram + replacement 6-card step summary ----------
svg = '''      <div class="pipeline-diagram-wrap" role="img" aria-label="Diagram: a job posting moves through six stages -- submit, preprocess, extract evidence, score, calibrate, explain -- to produce a credibility score.">
        <svg viewBox="0 0 940 150" xmlns="http://www.w3.org/2000/svg">
          <title>How a posting moves through JobCred, start to end</title>
          <!-- connecting arrows -->
          <g fill="none" stroke="#b7bcee" stroke-width="2.5">
            <line x1="110" y1="70" x2="180" y2="70"/>
            <line x1="270" y1="70" x2="340" y2="70"/>
            <line x1="430" y1="70" x2="500" y2="70"/>
            <line x1="590" y1="70" x2="660" y2="70"/>
            <line x1="750" y1="70" x2="820" y2="70"/>
          </g>
          <g fill="#b7bcee">
            <polygon points="180,65 180,75 192,70"/>
            <polygon points="340,65 340,75 352,70"/>
            <polygon points="500,65 500,75 512,70"/>
            <polygon points="660,65 660,75 672,70"/>
            <polygon points="820,65 820,75 832,70"/>
          </g>
          <!-- stage nodes: circle + icon + number badge, cx = 70,230,390,550,710,870 ; cy = 70 ; r = 34 -->
          <g>
            <!-- 1. Submit -->
            <circle cx="70" cy="70" r="34" fill="#eef1ff" stroke="#4f46e5" stroke-width="2"/>
            <g transform="translate(70,70)" stroke="#3f37c9" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <rect x="-9" y="-11" width="18" height="22" rx="2"/>
              <rect x="-3" y="-13" width="6" height="3" rx="1" fill="#3f37c9" stroke="none"/>
              <line x1="-5" y1="-5" x2="5" y2="-5"/>
              <line x1="-5" y1="0" x2="5" y2="0"/>
              <line x1="-5" y1="5" x2="2" y2="5"/>
            </g>
            <circle cx="92" cy="48" r="12" fill="#4f46e5"/>
            <text x="92" y="48" dy=".35em" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif">1</text>

            <!-- 2. Preprocessing -->
            <circle cx="230" cy="70" r="34" fill="#eef1ff" stroke="#4f46e5" stroke-width="2"/>
            <g transform="translate(230,70)" stroke="#3f37c9" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M-10,-9 L10,-9 L2,3 L2,10 L-2,10 L-2,3 Z"/>
            </g>
            <circle cx="252" cy="48" r="12" fill="#4f46e5"/>
            <text x="252" y="48" dy=".35em" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif">2</text>

            <!-- 3. Evidence extraction -->
            <circle cx="390" cy="70" r="34" fill="#eef1ff" stroke="#4f46e5" stroke-width="2"/>
            <g transform="translate(390,70)" stroke="#3f37c9" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <rect x="-9" y="-9" width="7" height="7" rx="1.4"/>
              <rect x="2" y="-9" width="7" height="7" rx="1.4"/>
              <rect x="-9" y="2" width="7" height="7" rx="1.4"/>
              <rect x="2" y="2" width="7" height="7" rx="1.4"/>
            </g>
            <circle cx="412" cy="48" r="12" fill="#4f46e5"/>
            <text x="412" y="48" dy=".35em" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif">3</text>

            <!-- 4. Model scoring -->
            <circle cx="550" cy="70" r="34" fill="#eef1ff" stroke="#4f46e5" stroke-width="2"/>
            <g transform="translate(550,70)" stroke="#3f37c9" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <line x1="-8" y1="-6" x2="8" y2="-6"/>
              <line x1="-8" y1="-6" x2="0" y2="8"/>
              <line x1="8" y1="-6" x2="0" y2="8"/>
              <circle cx="-8" cy="-6" r="2.6" fill="#3f37c9" stroke="none"/>
              <circle cx="8" cy="-6" r="2.6" fill="#3f37c9" stroke="none"/>
              <circle cx="0" cy="8" r="2.6" fill="#3f37c9" stroke="none"/>
            </g>
            <circle cx="572" cy="48" r="12" fill="#4f46e5"/>
            <text x="572" y="48" dy=".35em" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif">4</text>

            <!-- 5. Calibration -->
            <circle cx="710" cy="70" r="34" fill="#eef1ff" stroke="#4f46e5" stroke-width="2"/>
            <g transform="translate(710,70)" stroke="#3f37c9" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M-10,4 A10,10 0 0 1 10,4"/>
              <line x1="0" y1="4" x2="5" y2="-6"/>
              <circle cx="0" cy="4" r="1.8" fill="#3f37c9" stroke="none"/>
            </g>
            <circle cx="732" cy="48" r="12" fill="#4f46e5"/>
            <text x="732" y="48" dy=".35em" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif">5</text>

            <!-- 6. Explanation -->
            <circle cx="870" cy="70" r="34" fill="#eef1ff" stroke="#4f46e5" stroke-width="2"/>
            <g transform="translate(870,70)" stroke="#3f37c9" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <path d="M-10,-7 l2,2.4 l4.5,-4.5"/>
              <line x1="-1.5" y1="-7" x2="10" y2="-7"/>
              <line x1="-10" y1="0" x2="10" y2="0"/>
              <line x1="-10" y1="7" x2="5" y2="7"/>
            </g>
            <circle cx="892" cy="48" r="12" fill="#4f46e5"/>
            <text x="892" y="48" dy=".35em" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="'Plus Jakarta Sans', sans-serif">6</text>
          </g>
        </svg>
        <p class="pipeline-caption">Every posting follows this exact six-stage path, in this order -- nothing is skipped or special-cased.</p>
      </div>

      <div class="steps">
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Submit the posting</h3>
          <p>Paste the description text, plus any structured details you know -- title, location, salary, employment type. Anything left blank stays genuinely unknown, not guessed.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Preprocessing</h3>
          <p>The text and any structured fields are cleaned and standardised before anything is extracted from them -- the same step every posting goes through.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Evidence extraction (E1-E4)</h3>
          <p>The posting is scanned for four categories of evidence -- wording cues, identity cues, how complete the details are, and whether the text and fields agree -- producing 46 measured signals.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Model scoring</h3>
          <p>A fine-tuned language model reads the posting's text in context, and its reading is combined with the 46 evidence signals to produce one raw prediction.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Calibration</h3>
          <p>That raw prediction is passed through a calibration step so the final number genuinely behaves like a probability, then mapped to your 0-100 credibility score.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Explanation</h3>
          <p>A technique called SHAP ranks which pieces of evidence mattered most, turning the prediction into specific reasons, matched phrases, and a checklist to verify yourself.</p>
        </div>
      </div>'''

old_block = '''      <div class="steps">
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Submit the posting</h3>
          <p>Paste the description text, and fill in any structured details you know — title, location, salary, employment type. Anything left blank stays genuinely unknown, not guessed.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>The model reads it</h3>
          <p>A fine-tuned language model reads the text together with four categories of evidence — content cues, identity cues, metadata completeness, and text–metadata consistency — rather than judging the words in isolation.</p>
        </div>
        <div class="step-card">
          <div class="step-num"></div>
          <h3>Get a calibrated, explained score</h3>
          <p>The model\'s prediction is calibrated into a 0–100 credibility score, then explained with specific reasons, matched phrases, and a checklist of what to verify yourself.</p>
        </div>
      </div>'''

assert content.count(old_block) == 1, "old step block not found exactly once"
content = content.replace(old_block, svg, 1)

new_script_marker = content.count("const form = document.getElementById")
assert new_script_marker == orig_script_marker == 1, "script block marker changed -- aborting"

with io.open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("OK. bytes before:", orig_len, "after:", len(content), "delta:", len(content) - orig_len)
