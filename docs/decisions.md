# decisions.md — Design Decisions & Rationale

_Last updated: 2026-10-09_

> **What this file is.** One entry for every real design decision in my project: what I
> decided, what else I considered, why I went this way, and what it cost me. This is the
> file that answers the question every examiner asks — *"why did you do it that way?"*
>
> **How I use it.** Each entry ends with a **self-check** question. Before my viva I go
> through this file, cover the answer, and try to answer each self-check out loud in my own
> words. If I can't, I don't understand that decision well enough yet and I come back to it.
> The reasoning below is written the way I would explain it, so I have something concrete
> to test myself against.
>
> Format: newest at the top.

---

## 2026-10-09 — "for this posting" appended to every `_describe_feature()` template, after the merged "All observations" view surfaced a live example a user could genuinely misread as a general rule

- **Context:** testing the just-rebuilt results panel (previous entry) surfaced a real
  posting that scored **100/100, Low risk**, with **0% of structured fields filled in**, and
  four separate "All observations" lines all reading as "`<field>` was missing/blank, which
  **raised** the score" (location field-present, location-specificity, industry field, and
  `E3_completeness_score` itself all fired in the credibility-raising direction; only "an
  employer profile was missing" correctly read as lowering it). Read cold, those four lines
  say "leaving fields blank is good for your score" — a plausible, wrong, and actively
  harmful takeaway for an artefact whose whole second objective is explaining itself
  faithfully. This is the same pattern already logged above (the finders.lk 100/100 case) —
  this is a third live instance of it, now with the merged-observations view making it much
  more visible than the old three-separate-lists layout did.

- **Diagnosed, not assumed, before touching anything:** confirmed this is not a bug. SHAP is
  correctly reporting each feature's measured marginal contribution to THIS ONE prediction
  (KernelSHAP against `state.scaler.mean_` as background, same config Stage 7 validated) —
  it's a faithful local explanation of what the model actually learned from EMSCAD, not a
  computation error. Re-training or re-engineering features to force "intuitive" directions
  was explicitly ruled out: Stage 9 is closed (the test set is closed), and "fixing" the
  model's behaviour to match intuition would mean overriding what it actually learned, which
  is a methodological line I'm not willing to cross two weeks before submission just to make
  one screen read better.

- **So the fix is wording, not computation.** Split the problem in two, same as I talked
  through with the AI assistant before touching code: (a) is the model wrong — no; (b) is the
  *sentence* misleading on its own, out of context — yes, because "which raised the score"
  reads as a general claim and nothing in the sentence says otherwise.

- **What changed, in `_describe_feature()` (`src/api/pipeline.py`) only:**
  - Every one of its 13 return statements ends in the literal clause
    `, which {direction} the score.` — confirmed by grep (exactly 13 occurrences of
    `{direction} the score.` in the whole file, all inside this one function) before touching
    anything, so a single mechanical find-and-replace was safe and exhaustive rather than
    editing 13 branches by hand and risking missing one or wording one differently.
  - Replaced `{direction} the score.` → `{direction} the score for this posting.`
    everywhere, via one `replace_all`. Deliberately did **not** reword the "raised"/"lowered"
    part itself or restructure the sentences — appending a qualifier after the existing
    clause means the literal substrings `"raised the score"` / `"lowered the score"` are
    still byte-for-byte present, which matters because `frontend/index.html`'s
    `renderResults()` already parses those exact substrings to colour each "All
    observations" line red/green (see the previous entry). Checked this explicitly before
    editing — confirmed the frontend needed **zero** changes for this fix, which is the
    difference between a wording tweak and an afternoon of re-testing two coupled systems.
  - No change to feature engineering, SHAP computation, calibration, thresholds, or any
    numeric output. `credibility_score` and `risk_band` for every posting are bit-for-bit
    identical before and after this change — only the explanation strings changed.
  - `frontend/index.html`: added one static caveat line (plain `.muted-note` text, no new
    JS) above the "All observations" list: *"Each line reflects the model's reasoning for
    THIS posting only, not a general rule — the same detail (e.g. a blank field) can count
    differently on a different posting, depending on everything else in it."* Belt-and-braces
    with the per-line "for this posting" wording — the per-line fix catches someone who reads
    only one bullet, the caveat catches someone who skims the section as a whole.

- **Why the per-line fix over just a banner, or instead of it:** a single disclaimer at the
  top of the section is cheap but easy to skim past; the misleading claim is literally
  re-asserted on every line below it, so I wanted the correction present at the point of
  contact, not just once above it. Doing only the banner was the cheaper option I'd
  floated first; decided against it alone because it protects someone who reads the section
  header, not someone who reads one bullet mid-scroll and stops.

- **What I considered and explicitly rejected:** rewriting the 13 templates into full new
  sentences (e.g. "the model associated this with a higher score, specific to this posting")
  instead of just appending a suffix. More natural-sounding, but changes 13 full sentences
  instead of one shared literal, multiplies the surface area for a typo or an inconsistent
  tone across templates, and — critically — any phrasing that doesn't preserve the literal
  "raised the score"/"lowered the score" substrings breaks the frontend's existing red/green
  logic silently (everything would render as the 'neutral' grey/no-colour case, with no error
  thrown). Given the deadline, the minimal, mechanically-verifiable fix beat the more
  polished one.

- **Verified, not assumed, before pushing:** grepped `tests/` and `src/` on the actual
  machine for any test or script asserting these exact strings — none found; only
  `pipeline.py` itself and its own `__pycache__` reference `_describe_feature`, and the two
  smoke-test scripts (`stage8_smoke_test.py`, `stage8b_select.py`) just pass `top_reasons`
  through as data, no string assertions. `python3 -I` syntax-check on the edited file;
  isolated `exec()` of just `RULE_FIELD` + `_describe_feature()` run against five real
  sample inputs (including the exact `C2_field_present`/blank-location case from the
  screenshot, the fallback branch, and an `E3`/`E2` case) confirmed correct output text AND
  confirmed `"raised the score"` and `"lowered the score"` are both still present verbatim
  across the samples. Frontend: duplicate-id check, `getElementById` coverage check, and
  `node --check` on the extracted script all re-run clean after the caveat-line addition.
  Pushed to the actual files on the student's machine via `device_commit_files` with an
  `expectedMtimeMs` guard (not a blind overwrite), then independently re-verified via
  `sha256sum` run directly in the device's own shell (not just trusting the bridge's
  "written" response) before calling it done — both files matched the container's hash
  exactly.

- **One thing the student needs to do, that I can't do for them:** if the FastAPI server is
  currently running from an earlier session, it has the old `pipeline.py` already loaded in
  memory — Python doesn't hot-reload a running process's imports. The server needs restarting
  (or already runs with `--reload`) before this wording shows up in a live `/score` response;
  until then, new requests will still show the old phrasing even though the file on disk is
  already fixed.

- **What I gave up:** nothing measured — this is a strict subset of the existing explanation
  strings with four words appended. The only cost is 13 slightly longer sentences.

- **Revisit if:** Chapter 6 wants the fuller, non-mechanical reword (the rejected option
  above) once there's time to re-verify both files together properly instead of under
  deadline pressure.

- **Self-check:** *Why was it safe to fix this with one `replace_all` across 13 templates
  instead of editing each one individually — what specific thing did I check first that made
  that safe, and what would have made it unsafe?*

---

## 2026-10-09 — Frontend results panel restructured as a merged, report-style layout, deliberately NOT adopting jobscamscore.com's company/platform/scam-database verification sections

- **Context:** reviewed jobscamscore.com (14 screenshots) as a competitor/UX reference.
  Their results page is denser and more "report-like" than JobCred's: an executive-summary
  paragraph, a merged "All Observations" list instead of three separate flat lists, a
  staged loading screen, and paired red-flag/green-signal styling. But most of what makes
  their page feel authoritative — Company Verification (real website/LinkedIn/Glassdoor/
  Crunchbase lookups), "Listing Found on Platforms" (Indeed/ZipRecruiter/Monster
  cross-referencing), and Scam Reports (external scam-database checks) — depends on live
  external API calls JobCred's backend does not make. `pipeline.py` only computes E1–E4 from
  text and structured fields the user types in; there is no company/LinkedIn/platform/
  scam-database lookup anywhere in the codebase.

- **Decision: copy the presentation pattern, not the unverifiable content.** Building UI
  that shows "Company Website ✓ / LinkedIn Page ✓ / Found on 3 platforms" without a real
  check behind it would be fabricated verification — green checkmarks implying something
  never happened. This also directly re-opens a standing rule of this project: the external
  company-presence check is explicitly **API-only, qualitative, and excluded from the
  measured framework** (see the standing rules at the top of this file / `SKILL.md`) — it is
  not to be reintroduced as a fabricated or even a real fifth measured category in the UI.
  So nothing was added that isn't already one of the four fields `ScoreResponse` returns
  (`credibility_score`, `risk_band`, `top_reasons`, `suspicious_phrases`, `contradictions`,
  `verification_checklist` — see `schemas.py`). This was a presentation-only restructuring of
  `frontend/index.html`; zero backend changes, zero new fields.

- **What changed, concretely (all in `renderResults()` and the results markup):**
  1. **"Summary"** — a one-line, fully templated roll-up sentence (`Scored X/100 (Y risk).
     <top_reasons[0]>. N inconsistencies found... N suspicious phrases matched...`), built
     only from fields already rendered below it. Not a second model call, not an
     LLM-generated narrative like jobscamscore's — it cannot say anything the rest of the
     panel doesn't already show, by construction.
  2. **"All observations"** — merges `contradictions` and `top_reasons` into one list instead
     of the old three-section split ("Why this score" / "Suspicious phrases found" /
     "Inconsistencies found"). Contradictions are always shown as red flags with their rule
     tag. Each `top_reasons` string is colour-coded by parsing the *same* "raised the score" /
     "lowered the score" wording `pipeline.py`'s `_describe_feature()` already puts in the
     string (`direction = "lowered" if shap_value > 0 else "raised"`, confirmed in
     `pipeline.py`) — so the red/green split is reading an existing, already-signed piece of
     text, not a new judgement call invented in the frontend. A `top_reasons` entry that
     duplicates a contradiction's own `detail` string (pipeline.py seeds `top_reasons` with
     `contradictions[*].detail` first — confirmed in `build_explanation()`) is skipped so it
     isn't shown twice. Suspicious phrases render underneath as quoted chips (the literal
     matched text, unchanged from before).
  3. **"Recommendations"** — the old "Before you apply, verify" heading renamed; same
     `verification_checklist` data, no content change.
  4. **Loading stepper** — `/score` is one blocking request; the backend emits no per-stage
     progress events. The new stepper advances on a fixed 3.2s timer through labels
     describing the pipeline's real stage order (read text → check structured fields → run
     model → explain prediction), with a spinner (not a checkmark) on the current line, so it
     cannot be read as confirming any stage actually finished — it's a wait indicator, not a
     verified progress log. The existing honest copy ("the first check can take 10-20s while
     the model loads") was kept alongside it, not replaced.

- **Why this is acceptable to build at all, given the project only computes four evidence
  categories:** jobscamscore's density comes from two genuinely separable things —
  (a) more *data sources* (external lookups JobCred doesn't have), and (b) better
  *presentation* of the data already computed. Only (b) was adopted. The self-check for this
  is whether every new UI string traces back to an existing API field — it does; verified by
  grepping `schemas.py`'s `ScoreResponse` fields against every `data.*` access added to
  `renderResults()`.

- **Verified before deploying, same discipline as every prior frontend pass in this file:**
  no duplicate `id`s (checked programmatically, both the container copy and the file actually
  on the student's machine); `node --check` on the extracted `<script>` block (both copies);
  every `getElementById` target confirmed present in the markup; `buildPayload()` confirmed
  byte-identical to before (diffed, not eyeballed). Logic-level simulation of the new
  `renderResults()` against two mock `ScoreResponse` payloads (a flagged posting with a
  duplicate contradiction/top_reason pair, and a clean posting with zero contradictions and
  zero suspicious phrases) confirmed: the duplicate contradiction text is shown exactly once
  (as the red flag with its rule tag, not twice), `raised`/`lowered` wording maps to
  signal/flag correctly, and the "No single feature dominated..." fallback renders as
  neutral rather than crashing or defaulting to red. Pushed to the actual file on the
  student's machine via `device_commit_files` (not retyped through the chat — an earlier
  attempt at hand-transcribing a patch script round-tripped a comment with a doubled
  parenthesis, which is exactly the class of silent corruption this discipline exists to
  catch) and confirmed byte-for-byte via `sha256sum` on both sides after the push
  (`29f8e5f4...` on both), plus a second `sha256sum` + `grep` check on the device's shell
  directly (not just the bridge's own "written" response) before calling it done.

- **What I gave up:** none of jobscamscore's external-verification sections. That's a
  deliberate scope decision, not an oversight — building real Company/LinkedIn/platform/
  scam-database checks would mean adding exactly the fifth measured category this project's
  standing rules already closed off, on top of needing live third-party API access this
  project doesn't have budget or scope for in the time remaining.

- **Revisit if:** a future iteration of this project explicitly adds a real (not fabricated)
  external verification layer as a *separate*, clearly-labelled, non-measured feature — the
  same boundary the existing "external company-presence check" rule already draws.

- **Self-check:** *Why does the red/green colour on each "All observations" line not count as
  a new, invented judgement — what in `pipeline.py` already determines it before the
  frontend ever sees the string?*

---

## 2026-10-09 — Frontend UX polish: Clear-form button, styled file-upload button, and a
copy pass over the status/error messages — display only, no scoring logic touched

- **Context:** three requests after the explainability-wording fix above — (1) no way to
  clear the form without reloading the page, (2) the native "Choose File" button for the
  screenshot upload had no styling at all, clashing with the rest of the page, (3) a general
  ask to review every visible message for tone/clarity, with several already-live strings
  quoted back as the standard to match.

- **Clear-form button:** added `button#clearBtn` next to the submit button inside a new
  `.form-actions` flex row (submit keeps most of the width, clear is a smaller neutral
  outline button that turns red-tinted on hover, signalling "this resets everything" without
  being alarming by default — same visual language as the rest of the page). Its handler
  calls the browser's native `form.reset()`, closes the "Add more details" panel, and clears
  the result panel / status / error text — nothing else. It does not call `buildPayload()`,
  `renderResults()`, or touch the submit handler in any way; it's a fully independent click
  listener added right before the existing submit listener.

- **File-upload button styling:** restyled via `::file-selector-button` /
  `::-webkit-file-upload-button` (the real, standard CSS hook for this exact problem) plus a
  themed border/background on the input itself, matching the other form fields. Deliberately
  NOT replaced with a hidden-input-plus-label fake button — that pattern needs new JS to keep
  `imageInput.files[0]` wired to a visible trigger, which is unnecessary risk for a purely
  cosmetic request when the standard pseudo-element does the same job with zero JS changes.

- **Copy pass:** of the quoted "approved" strings, every one was already live verbatim — no
  change needed there. Tightened the ones NOT quoted (all in the URL-fetch/screenshot-OCR
  click handlers and the submit error paths): "Paste a URL first." →
  "Paste a job posting URL first."; "Choose an image file first." → "Choose a screenshot
  first."; the various "Could not reach/read/fetch..." strings reworded to "Couldn't ...,
  then try again." for a slightly warmer, more consistent register; the raw
  `Request failed (HTTP ...)` prefix softened to `Something went wrong (HTTP ...)` while
  keeping the actual status code and server detail intact (still useful for debugging, just
  less alarming as a first line). No status/error string was removed or made less
  informative, only reworded.

- **Verified before deploying, same discipline as the two earlier frontend passes
  (2026-10-09, "visual redesign" addenda, this file further below):** no duplicate element
  `id`s (38 unique, checked programmatically); every opening/closing structural tag pair
  balanced (div/section/form/header/footer/main/script/style/svg/details/select/label/
  button/nav); every id the JS references via `getElementById` is actually present in the
  markup (21 checked, 0 missing); `buildPayload()` confirmed byte-identical to before;
  `renderResults()` and the submit handler's core fetch/payload logic confirmed unchanged by
  direct string match, not just "looks right." Pushed to the device and verified by
  `md5sum` before telling the student it was done (matched on the first attempt this time).

- **What I gave up:** nothing functional. Pure presentation and wording.

- **Self-check:** *why does `form.reset()` safely clear the URL/image inputs too, even
  though they're not part of `buildPayload()`'s field list — what makes them "form
  elements" in the same sense as the scored fields?*

---

## 2026-10-09 — Found, and the student independently confirmed with a controlled test: the
score is sensitive to whether the job-title field is filled in, holding the suspicious text
fixed — flagged as a limitation, not fixed

- **What happened:** the student ran the same hand-written scam text (see the earlier
  "worst case" testing addenda below) through `/score` twice, identical in every way except
  the "Job title" field: blank the first time, `"Data Entry Assistant"` the second. Scores:
  **82/100 Low risk** (no title) vs. **29/100 High risk** (with title) — a large swing from
  one short, unremarkable field.

- **Mechanism, verified against the real code, not guessed:** `train_baseline.py`'s
  `_build_text()` — which `pipeline.py`'s own docstring already names as "the same text
  scope as training" — joins `title + description + requirements + benefits` into ONE
  string before it ever reaches DistilBERT. So "title present vs. blank" isn't cosmetic
  metadata; it changes the literal input sequence the text encoder reads. Given this
  project's own earlier finding (Stage 8b, logged below) that the text-embedding pathway is
  the dominant, SHAP-unexplained half of the final score, a changed text sequence producing
  a changed score is mechanically expected.

- **What is NOT established:** *why* adding a short, ordinary job title flips the verdict
  this much in this direction. I can't inspect DistilBERT's attention weights or run the
  real model myself to test further hypotheses — I only confirmed WHERE the sensitivity
  enters (the concatenated text input), not WHY a two-word addition has this much leverage
  over the output. This is consistent with a known property of fine-tuned transformer
  classifiers in general (sensitivity to small, semantically-minor input changes), not
  necessarily specific to this model or a sign of a bug.

- **Why not "fixed":** there's nothing to fix in the code — the title field is correctly
  being used exactly as it was during training, matching the trained artefact exactly.
  "Fixing" this would mean changing what the model responds to, which is a retraining
  question, and Stage 9 is closed. This is a genuine, now-evidenced limitation of the
  trained model's robustness, not a software defect.

- **Why this is worth more than a one-off oddity:** it's the third live result (after the
  two earlier synthetic tests, see addendum below) where small input changes produced score
  swings that don't obviously track "more scam-like" vs. "less scam-like" in an intuitive
  way. Combined with the real finders.lk posting scoring 100/100 while every listed
  structured reason pointed toward missing information — this is becoming a pattern worth
  reporting honestly in Chapter 5 (limitations/discussion), not three unrelated surprises.

- **What I did NOT do:** re-run Stage 9, retrain, or change any model/feature/threshold —
  all out of bounds per the closed-test-set guardrail. This entry documents a finding from
  live, informal, post-hoc testing, which is demonstration, not evaluation.

- **Self-check:** *why does "the title field is being used exactly as trained" make this a
  limitation to report rather than a bug to fix, and what would have to be true for it to
  become a bug instead?*

---

## 2026-10-09 — "Why this score" no longer leaks raw internal feature names for C1-C6

- **Context:** while testing live, I saw bullets reading literally `The 'C2_field_present'
  signal lowered the score.` / `The 'C5_field_present' signal raised the score.` — a code
  column name shown straight to an end user, unreadable without reading the source. Traced
  the cause before touching anything: `_describe_feature()` in `src/api/pipeline.py` has
  hand-written plain-English templates for every E1/E2/E3 feature, but none for any C1-C6
  feature or for `E4_contradiction_count` — anything untemplated falls through to a generic
  `f"The '{name}' signal {direction} the score."` line, which just prints the raw column
  name. 13 features had this gap: `C{1..6}_field_present`, `C{1..6}_evaluable`, and
  `E4_contradiction_count`.

- **What I decided (three changes, all in `_describe_feature()` / `build_explanation()`,
  nothing else):**
  1. `C{i}_field_present` → templated using the already-existing `RULE_FIELD` dict (same
     dict the Contradiction objects already use), e.g. *"The posting's 'required education'
     detail was left blank, which lowered the score."* Same wording pattern as the existing
     E3_*_present template.
  2. `E4_contradiction_count` → templated, e.g. *"2 of the posting's details didn't match
     what the text said (out of up to 6 checked), which lowered the score."*
  3. `C{i}_evaluable` → **excluded from "Why this score" entirely**, via a new
     `_is_bookkeeping_feature()` check in `build_explanation()`'s ranking loop (same
     `continue`-and-skip pattern already used to exclude a fired rule's own
     `C{i}_contradiction` feature). This one isn't a wording fix — it changes what's shown.
     `evaluable` means "could this rule even be checked" (field present AND recognisable
     text language to compare it to), not "is this suspicious." There's no honest sentence
     that makes "could we check this" read as a reason, so rather than write a misleading
     one, I left it out. If it previously occupied one of the 5 "why this score" slots, a
     different, lower-ranked feature now takes that slot instead — the score and the SHAP
     ranking itself are unchanged, only which reasons get displayed.

- **Why safe to do now, with Stage 9 closed:** this is string-template and display-filter
  code only — no change to the model, SHAP computation, calibration, the score itself,
  `/score`'s request/response contract, or any stored Stage 9 result file. Verified before
  touching the device copy: (a) `python -m py_compile` on the edited file; (b) an isolated
  test (`_describe_feature`/`_is_bookkeeping_feature` sliced out of the real file and exec'd
  standalone, since the full module needs torch/shap not installed in my sandbox) — 40/40
  checks: all 6 `field_present` templates in both presence states and both SHAP directions,
  `E4_contradiction_count` at two values, all 6 `evaluable` features confirmed excluded,
  `field_present`/`contradiction` features confirmed NOT wrongly excluded, and — the
  important regression check — the existing E1/E2/E3 templates produce byte-identical
  output to before. Then committed straight to the device copy (no manual retyping).

- **What I gave up:** showing *something* for `evaluable` rather than nothing. A translated
  sentence would have been more "complete," but "complete and misleading" is worse than
  "incomplete and honest" for a field that isn't itself evidence.

- **Self-check:** *why is `C{i}_field_present` a real reason a reader should see, while
  `C{i}_evaluable` is not — what's the actual difference between "was this detail given"
  and "could we check this detail against the text"?*

- **Addendum, same day — asked directly "are all of these fixed now," so I checked
  exhaustively instead of assuming the first pass was complete:** reconstructed the exact
  list of all 46 structured feature names from `train_distilbert.py`'s own
  `STRUCTURED_FEATURE_GROUPS` spec (not retyped from memory) and ran every one through
  `_describe_feature()`. Found two more real gaps the first pass missed, both in the same
  family: `C{i}_contradiction` itself falls back to the raw name **when the rule did NOT
  fire** (value 0) — the existing `covered` exclusion only hides it for a rule that DID
  fire, where its evidence string is shown instead; a non-fired contradiction feature can
  still be SHAP-ranked as a reason (e.g. "no mismatch" being reassuring) and was still
  hitting the raw-name fallback. And `C6_text_salary_field_absent` (the supplementary C6
  signal — field absent but text names a dollar figure anyway) had no template at all.
  **Fixed both** with the same templating approach (reusing `RULE_FIELD`). Re-ran the
  exhaustive 46-feature check afterward: 40 features now have real templates, 6
  (`C{i}_evaluable`) are deliberately hidden, 0 fall back to a raw name — confirmed
  programmatically, not just spot-checked against the two names the student happened to
  see. Also hit the same silent device-write failure as before (`device_commit_files`
  reported success twice with no actual change on disk) — confirmed via `md5sum` on the
  device both times before trusting it, third attempt actually took.
  - **Self-check:** *why did checking only the two feature names I'd personally seen fail
    to catch the other two gaps, and what does "validated" actually require — spot-checking
    the cases reported, or enumerating the full feature space the code can produce?*

---

## 2026-10-09 — URL and screenshot input added as pre-fill conveniences, not as changes to
/score, ScoreRequest, or the trained pipeline

- **Context:** with development otherwise complete and Stage 9's test set closed, the
  student asked whether two convenience inputs could still be added without undoing any of
  that: (1) paste a job-posting URL, (2) upload a screenshot/image of a posting. Both were
  requested together, with explicit instruction that the already-working development must
  not be harmed.

- **Decision:** added two new, purely additive FastAPI routes — `POST /extract-url` and
  `POST /extract-image` — plus two new Pydantic models (`UrlExtractRequest`,
  `ExtractResponse`) in `schemas.py`. Both routes do exactly one thing: return extracted
  text (and a title, for the URL case) for the frontend to drop into the *existing* `text`/
  `title` fields, for the user to read and edit before pressing the *existing* submit button
  that calls `/score`. Nothing is auto-submitted. `ScoreRequest.url` and `/score`'s own
  `if request.url: raise HTTPException(501, ...)` stub are untouched — these new routes do
  not implement that field, they sit entirely outside it.

- **Why this doesn't reopen or contradict the 2026-08-07 decision ("Make raw text the
  primary API input, with URL support best-effort only"):** that decision was about what
  the *scored artefact* accepts as input — and it still only accepts raw text (plus the
  optional structured fields), unchanged. These two new routes are acquisition conveniences
  that sit in front of that same text box, not a second input path into the model. The
  2026-08-07 reasoning (ToS risk, page-structure fragility) is exactly why these are kept
  separate from `/score` and framed as best-effort, reviewable pre-fill rather than silent
  auto-ingestion.

- **Options considered (URL fetching):**
  - (A) Wire a real fetch into `ScoreRequest.url` / the `/score` 501 stub directly.
    Rejected — this would make the scored artefact's behaviour depend on a fetch outcome
    outside Stage 9's already-closed, tested/validated pipeline, and would blur the
    "demonstration vs evaluation" line the project guardrails insist on keeping separate.
  - (B) A separate `/extract-url` endpoint, text handed back for review. **Chosen.**
  - For which sites to allow: (i) hardcode a small allowlist of known-good sites, or
    (ii) check each site's own `robots.txt` at request time via `urllib.robotparser`, with
    a small hardcoded exclusion list only for sites that are technically fetchable but
    contractually/practically wrong to fetch anyway. **Chose (ii) + a one-item exclusion
    list (LinkedIn)** — robots.txt is the site's own stated policy and generalises to sites
    never tested (this is what makes topjobs.lk get excluded automatically, without needing
    it hardcoded); LinkedIn is excluded outright on top of that because its job pages are
    client-side rendered, so the posting text is not present in the static HTML
    `trafilatura` would fetch, and separately because scraping LinkedIn breaches its ToS.

- **Options considered (OCR engine):** `pytesseract` (wraps the system Tesseract binary) vs
  `easyocr` (pure-pip, no system binary, could reuse the student's existing
  CUDA/torch stack). Tested `pytesseract` directly against all 8 of the student's real
  example job-ad images — results were consistently clean and highly readable. **Chose
  `pytesseract`** on that measured result, even though it costs the student a one-time
  system-level Tesseract install on Windows (not just `pip install`) that I cannot perform
  remotely. `easyocr` was not run head-to-head against the same images — the decision is
  "pytesseract measured good enough," not "pytesseract beats easyocr," which would be an
  unmade comparison.

- **What I gave up / what remains unverified:**
  - I could not personally execute a real fetch against any external job site from any
    tool available to me in this session — my own sandbox and the device's Linux VM both
    hit identical `403 Forbidden` / "Tunnel connection failed" errors from their own
    outbound proxies when I tried `ikman.lk` directly. The `/extract-url` route's logic
    (exclusion check, robots.txt check, trafilatura wiring, error handling) was verified
    with mocked network calls in my own sandbox (`test_new_routes.py`, 11/11 checks
    passed) and reasoned about using WebFetch as an imperfect proxy signal against the
    student's 6 real URLs earlier in this session — but its real-world behaviour against
    real sites has NOT been run end-to-end by me. `src/api/live_extract_check.py` is the
    standalone script (same pattern as the existing `live_api_check.py`) for the student
    to run themselves, with real network access, to get that real signal.
  - `pytesseract`'s quality test used only the 8 images already in hand, not a broader
    sample — "works well on these 8" is the actual, honest claim, not "works on all
    screenshots."
  - The Tesseract binary install is a manual, one-time step on the student's own machine
    (documented separately) that I cannot do for them.

- **Revisit if:** either route turns out to fail on the majority of the student's actual
  demo sites/images when they run the real checks themselves — in which case the honest
  move is to report the limitation in the thesis, not to keep tuning against the 8 images.

- **Self-check:** *Why doesn't adding `/extract-url` reopen the 2026-08-07 decision to keep
  URL input out of `/score`, and what specifically did I never verify myself about this
  feature?*

- **Addendum, same day — real `pip install` caught a dependency conflict I missed:** when
  the student ran `pip install -r requirements.txt` on the real machine, pip reported
  `ResolutionImpossible`: `trafilatura==2.3.1` actually requires `charset_normalizer>=3.5.2`,
  `lxml>=6.1.3`, and `urllib3>=2.8.0`, but I had only checked that `trafilatura==2.3.1`
  itself existed on PyPI, not its own dependency floor against the versions already pinned
  in `requirements.txt` (`charset-normalizer==3.5.1`, `lxml==6.1.2`, `urllib3==2.7.0`). Fixed
  by bumping those three pins to the exact minimums trafilatura needs, and explicitly
  pinning trafilatura's own new transitive dependencies (`babel`, `courlan`, `dateparser`,
  `htmldate`, `justext`, `lxml_html_clean`, `pytz`, `tld`, `tzlocal`) at the versions a clean
  resolver picked — matching this file's existing convention of pinning every transitive
  dependency, not just top-level ones. Verified this time with a real `pip install
  --dry-run` against the exact final `requirements.txt` in a fresh venv (not just checking
  version existence) — resolved cleanly, "Would install" the full closure, zero conflicts.
  **Lesson for next time:** when adding a new pinned dependency to an already-pinned
  requirements file, check its dependency floor against the existing pins before handing it
  to the student, not just that the version string resolves.

- **Addendum, same day — real-world URL testing found two more real problems, both fixed:**
  the student ran all 6 of their real candidate URLs through the live `/extract-url` route
  for the first time (something I could not do myself, per the addendum above). Results:
  **ikman.lk worked perfectly** (clean title + text, scored correctly end to end) --
  the first genuine, live, external confirmation this feature actually works, not just
  reasoned-about. **LinkedIn was correctly rejected**, as designed. But two real problems
  surfaced:
  1. **topjobs.lk was NOT rejected, and shouldn't have let through either way.** The
     robots.txt check (the general mechanism meant to catch exactly this site) let it
     through -- I confirmed separately, by trying the exact same URL from my own tools,
     that its robots.txt DOES disallow at least some crawlers from that page (I got
     `ROBOTS_DISALLOWED` myself). The per-user-agent robots.txt rule my code checks
     against evidently isn't the one that caught it. Worse, independent of the robots.txt
     question, what got extracted wasn't the job posting at all -- it was account/
     navigation chrome ("Apply by email", "create your personalised digital CV"). **Fix:**
     hardcoded `topjobs.lk` into the same exclusion list as LinkedIn, rather than trying to
     debug robots.txt per-user-agent matching edge cases under today's deadline. This also
     fixes the bad-content problem for free, since the site is now rejected outright.
  2. **xpress.jobs "succeeded" but returned garbage.** The extracted "text" was the literal
     client-side fallback string `"You need to enable JavaScript to run this app."` --
     confirms the earlier suspicion (xpress.jobs is JS-rendered) but the route returned
     this as a 200 success instead of catching it. **Fix:** added a content-quality check
     before returning a result -- reject (422, clear message) if the extracted text is
     under 100 characters or contains a known JS-required placeholder phrase. This is a
     general guard, not a site-specific patch, so it should also catch other JS-rendered
     sites not yet tested, though that's untested, not guaranteed.
  - **Verified in my own sandbox, not just reasoned about this time:** re-ran the full
    route through `test_new_routes.py`'s harness with 2 new cases (topjobs.lk-shaped URL
    now correctly rejected; a mocked "enable JavaScript" response now correctly rejected)
    plus a regression check that a real, well-formed posting (the same shape as the
    student's working ikman.lk case) still succeeds. 6/6 passed.
  - **What this means for the write-up:** the honest claim for this feature is "worked
    cleanly on ikman.lk, correctly declined LinkedIn and (now) topjobs.lk, and now gives a
    clear error instead of garbage on JS-rendered sites like xpress.jobs" -- not "works on
    all sites." This is exactly the kind of result a research prototype should report:
    real, mixed, and not cherry-picked to the one case that worked first.
  - **Self-check:** *Why did I trust robots.txt as the general mechanism, and what did the
    real test show about that trust?*

- **Addendum, same day — broad real-world test across 13 real Sri Lankan/international job
  sites, after the topjobs.lk/xpress.jobs fixes above:** the student tested well beyond the
  original 6 candidate URLs. Results:
  - **Extracted cleanly (8 sites):** ikman.lk, finders.lk, rooster.jobs, jobpal.lk,
    jobeka.lk, itpro.lk, dreamjobs.lk. **skyjobs.lk** returned only minimal text via
    `/extract-url` (the posting is apparently mostly image-based on that site) -- the
    student used `/extract-image` (screenshot) on the same posting instead and it worked.
    This is a real demonstration of why both features exist, not just one: they cover
    different failure modes of the same underlying problem (getting posting text into the
    box for review).
  - **Correctly declined, exactly as designed (4 sites):** LinkedIn and topjobs.lk
    (hardcoded exclusion), xpress.jobs (content-quality guard), and **unjobs.org** --
    caught by the general robots.txt mechanism on its own, with no special-casing needed.
    This is useful evidence the robots.txt check *does* work as a general mechanism --
    topjobs.lk was the one site where it didn't, not proof the whole approach is unreliable.
  - **Failed, but gracefully (1 site):** Indeed -- clean "could not reach the URL, or the
    site blocked the request" message, not a crash. Expected: Indeed is a major aggregator
    that blocks most automated access.
  - **Net result:** 8 of 13 real sites tested extract cleanly; every failure mode produced
    a clear, honest message rather than a crash or silently-wrong result (after the two
    fixes above). This is the actual, defensible claim for the thesis: broad coverage
    across real local job boards, honest and non-crashing behaviour on the rest, not "works
    everywhere."
  - **Self-check:** *What's the difference between a site "not supported" and a site
    exposing a bug, and how do I tell them apart from the error message alone?*

- **Addendum, same day — Timesjobs.lk confirmed clean, closing out real-world testing:**
  the one unclear result from the addendum above is resolved: Timesjobs.lk gives a clean
  `"www.timesjobs.lk's robots.txt disallows automated access to this page."` message, not
  a crash -- the general robots.txt mechanism catching a second site on its own (after
  unjobs.org), with no special-casing needed. (Separately, that posting's actual content
  is itself an image on the page, not text -- so even an allowed fetch wouldn't have
  recovered real text there without OCR; not actionable, just noted.) **Final tally across
  13 real sites tested: 8 extract cleanly, 5 declined or failed with a clear message, 0
  crashes.** Real-world testing of both pre-fill features is now complete.
  - **Self-check:** *Across the 13 sites tested, which failures were "mechanism working as
    designed" versus "bug Claude had to fix," and how would I tell an examiner the
    difference in one sentence?*

---

## 2026-10-09 — Research objectives and questions reworded to v4 (plain-language, thesis
1.3/1.4), RQ3 corrected for precision against the now-closed Stage 9 test set

- **Context:** the student brought a finalised, plain-language rewording of the project's
  five objectives and five research questions for the thesis's 1.3/1.4 sections, asking
  whether it still aligns with what was actually built and evaluated. Checked each
  objective/RQ individually against the real Stage 1—9 work (not against memory of what
  was planned).
- **Four of five pairs aligned cleanly as written:** O1/RQ1 (taxonomy, Stage 2 manual
  audit), O2/RQ2 (baseline model, Stage 5 + Stage 9 Part 1 — the "compare with published
  studies" clause is a Chapter 5 writing task against sources the literature review already
  cites, not a development gap), O4/RQ4 (explainable decision module, Stage 7 SHAP + Stage 4
  consistency rules + Stage 8 API), O5/RQ5 (evaluation, Stage 6/9 — this version explicitly
  names explanation-faithfulness checking as part of evaluation, which is real, already-
  measured work from Stage 7 (SHAP vs. random-ranking control, 100% rule-consistency) that
  the original v3 wording didn't call out explicitly; a genuine improvement, not just a
  rewording).
- **One real ambiguity found, not just a style issue: RQ3.** The student's first draft read
  "...added to a text-based model, compared with a text-only baseline." That phrase is
  genuinely ambiguous between two different comparisons:
  - **(A)** the O2 baseline (TF-IDF + classical classifiers) — already measured in Stage 9
    Part 1 (full multi-signal model vs. TF-IDF baseline, 3 seeds each). No new work needed.
  - **(B)** a transformer-only, zero-structured-evidence condition, holding the text encoder
    constant and removing all four evidence categories at once — this exact condition was
    **never run**. Stage 9 Part 2's ablation removes evidence categories one at a time
    (E1, E2, E3, E4, has_company_logo individually), which answers a different question
    (each category's individual marginal contribution within the full model), not "what
    does the full model gain over a bare transformer."
  - This distinction matters because Stage 9's test set is already closed under the
    "test used once" guardrail (logged 2026-10-08, before any test number was seen) —
    if (B) were the intended claim, it could not be satisfied by any experiment run so far,
    and none can be run now.
- **Decision, made explicitly by the student:** keep development exactly as it is; adjust
  wording only. Confirmed Reading (A) is what's actually being claimed (O3's own v3 wording
  already said "compared with the baseline model", unambiguously (A) — only RQ3's phrasing
  had drifted). RQ3 reworded to mirror O3's language exactly: "...compared with the baseline
  model, under matched conditions" — removing "text-based model" / "text-only baseline",
  which read like (B).
- **What was given up:** nothing. No experiment, no code, no model. Pure wording precision,
  decided before the wording was locked into the actual thesis document, rather than being
  caught by an examiner after submission.
- **Implementation:** `project.md`'s "Research objectives" / "Research questions" sections
  replaced wholesale with this v4 wording (marked "supersedes v3", v3 wording kept
  nowhere else in that file so there's no stale duplicate). A note flags that
  `Research_Objectives_and_Questions_Final.docx` still shows v3 as of this entry and needs
  updating separately to match.
- **Self-check:** *If an examiner asked "what, exactly, is 'the baseline model' in RQ3?",
  can you answer in one sentence without having to explain away an ambiguity? (You should
  now be able to: it's the TF-IDF + classical-classifier model from O2/RQ2, evaluated in
  Stage 9 Part 1.)*

---

## 2026-10-09 — Minimal manual-entry frontend added, reopening the "backend API only"
scope decision on purpose, not by drift

- **Context:** manually testing the live API (via Swagger `/docs` and curl) surfaced a real
  usability gap: a real user has a pasted paragraph or a link, not a 17-field JSON body.
  `project.md`'s own Scope section lists "Frontend UI (backend API only)" under **Out of
  scope** — this is a deliberate reopening of that decision, not an oversight, logged as
  such rather than silently built.
- **The actual question wasn't "frontend or not" — it was what the frontend is allowed to
  do with the user's pasted text.** A frontend that auto-splits one pasted blob into
  title/location/salary/etc. is the exact same heuristic Decision "Stage 8 wiring"
  (2026-10-08) already considered and rejected as Option C: *"an untested, unvalidated
  heuristic the model was never trained or tested against — it would silently create a
  train/inference mismatch worse than honestly leaving a field missing."* Moving that same
  guess from backend to frontend doesn't remove the risk, it just relocates it.
- **Options considered:** (A) no frontend, document the gap as a limitation and move on;
  (B) a minimal manual-entry form — separate labelled fields the human fills in directly
  (same principle as a real job-board submission form), zero auto-parsing, calls the
  existing `/score` unchanged; (C) a "smart" form that pre-fills fields from pasted text via
  heuristics, user reviews/edits before submit; (D) URL auto-fetch-and-parse.
- **Decision:** (B). Raised to the student directly (`AskUserQuestion`, 2026-10-09) given
  this reopens an explicit scope line under a near-term deadline — not treated as a routine
  engineering call under the standing delegation, since it changes what gets built, not how
  an already-agreed piece gets built. Student chose B explicitly, emphasising "without
  harming current working project."
- **Why B over C or D:** C still ships an unvalidated heuristic to the user, just dressed as
  a "suggestion" — the risk is softened, not removed, and it's real extra work for a benefit
  this project doesn't need to claim. D reopens the URL-scraping/ToS question Decision
  (2026-08-07, "Make raw text the primary API input") deliberately avoided, for reasons that
  still hold. B needs no new heuristic, no new dependency, and cannot touch model behaviour
  at all — it only changes how a human supplies values that were already optional inputs.
- **Implementation, kept deliberately low-risk:** `frontend/index.html` — a single
  self-contained static page (inline CSS/JS, no build step, no new Python dependency),
  served by one new additive route (`GET /` in `src/api/main.py`, `include_in_schema=False`
  so it doesn't appear in the Swagger contract). Served same-origin from the same FastAPI
  app specifically so no CORS configuration is needed. The page builds its JSON payload by
  only including a field if the user actually typed something into it — an empty field is
  omitted from the request entirely, not sent as `""` or a guessed value, preserving
  `ScoreRequest`'s existing "optional, genuinely missing if not supplied" semantics exactly.
  `/score`, `/health`, `pipeline.py`, and every trained-model code path are untouched.
- **What I gave up:** a documented, named limitation that would otherwise have been simple
  to write up and leave alone. In exchange, the artefact is now actually usable by someone
  who isn't comfortable hand-writing JSON — closer to what a real deployment would need.
- **Self-check:** *Why does moving the "split pasted text into fields" logic into a frontend
  not make it safer than doing the same guess in the backend — and what makes option B
  immune to that specific risk in a way option C isn't?*

### Addendum (2026-10-09, same day) -- visual redesign of the same frontend, no field or
  logic changes

- **Context:** once the manual-entry form (above) was working, the request was to make the
  same page "next level and fully attractive," full-screen, mobile-responsive, with
  https://jobscamscore.com/ as a style reference. This is a visual-design iteration of the
  decision already logged above, not a new functional or scope decision -- logged as an
  addendum rather than a fresh entry.
- **What changed:** `frontend/index.html` was rewritten as a styled single-page layout --
  sticky header/nav, a dark hero section, the same form moved into an elevated "scan card,"
  an animated SVG score-ring in place of the old plain coloured circle, phrase/risk chips in
  place of plain list items, plus three added marketing-style sections ("How it works," an
  "Evidence model" section describing E1-E4 descriptively (no invented numbers or claims),
  and a plain, modest "about" paragraph identifying it as a final-year research artefact).
  Mobile responsiveness via CSS media queries (640/760/860/980px breakpoints) and
  `clamp()`-based fluid type; no JS framework, no build step, no new dependency.
- **What did NOT change, verified before deployment:** every field `id` the JS reads
  (`text`, `title`, `company_profile`, `requirements`, `benefits`, `location`,
  `salary_range`, `employment_type`, `department`, `required_experience`,
  `required_education`, `industry`, `function`, `telecommuting`, `has_company_logo`,
  `has_questions`) is unchanged from the first version. `buildPayload()`'s omit-if-empty
  logic -- the part that preserves `ScoreRequest`'s genuinely-missing semantics -- is
  byte-for-byte the same function, only the result-rendering code was rewritten to animate
  the new SVG ring instead of recolouring a plain div. `/score`, `/health`, `pipeline.py`,
  and `src/api/main.py`'s route itself (still `GET /`, still `include_in_schema=False`) were
  not touched a second time.
- **Verification before deployment:** checked the rewritten file for duplicate element
  `id`s (none) and balanced opening/closing tags for every structural element (div,
  section, form, header, footer, main, script, style, svg -- all matched) before pushing it
  to the device, specifically because this file merges two design iterations and that is
  exactly the kind of change where a leftover duplicate id or an unclosed tag silently
  breaks the JS without raising an error.
- **What I gave up:** nothing functional -- this is presentation only. The cost is pure
  styling effort; no new risk to the trained model, the API contract, or the
  genuinely-missing-field semantics the earlier decision protected.
- **Self-check:** *If you temporarily deleted every line of CSS from this file, would the
  underlying form still collect and submit exactly the same JSON payload as the first
  version? (It should -- styling and data-collection were kept strictly separate on
  purpose.)*

### Addendum 2 (2026-10-09, same day) -- second visual pass: naming, copy, and polish,
  still no field or logic changes

- **Context:** after seeing the first redesign, the feedback was that the input fields
  looked flat/mismatched against the dark hero, the page needed a real product name, the
  placeholder example ("Coordinator") should be something more universally recognisable,
  the section copy should read less like internal jargon, and the project needed a visible,
  properly-placed academic attribution. This is a second iteration on the same decision
  above, not a new scope or functional change.
- **Naming:** named the page "CredLens" -- a short, literal name (credibility + the idea of
  a lens/inspection) that ties to the "Explainable AI" framing already used elsewhere in the
  project, rather than an invented buzzword. Used consistently in the page `<title>`, header
  logo, and footer.
- **Visual fixes:** gave inputs/selects/textareas a distinct light-indigo tint
  (`--input-bg`) and an inset shadow instead of a near-white background that was barely
  distinguishable from the white card behind it; added a brand-gradient accent strip to the
  top of the "scan card" and an indigo-tinted glow in its shadow so the white card reads as
  part of the same blue theme as the dark hero instead of looking like an unrelated flat
  white box dropped onto it; replaced the ALL-CAPS tracked-letter-spacing style previously
  used for "Why this score" / "Suspicious phrases found" / etc. with sentence case plus a
  left accent bar, and removed the same ALL-CAPS treatment from the "How it works" /
  "Evidence model" section eyebrows -- both were flagged against this project's own
  frontend-design guidance as a generic templated-AI tell, not a deliberate choice for this
  brief.
- **Copy:** rewrote the hero headline to state the product's actual deliverable ("A
  credibility score for every job posting") instead of a single-word-accented slogan;
  rewrote the evidence-model and how-it-works card copy in plainer, less jargon-heavy
  language aimed at a job seeker rather than an engineer; changed the job-title placeholder
  from "Coordinator" to "Software Engineer" as requested.
- **Attribution:** added a footer block naming the author and the academic context in the
  conventional place for authorship credit (page footer, not the marketing hero) --
  "Developed by Oshadha Samarasinghe (O.K. Samarasinghe) for a BSc (Hons) Computing
  final-year research project", with the registration details (Coventry University / NIBM,
  COBSCCOMP242P-069, 16116041) on a second line, kept separate from the project-description
  paragraph in the "About this project" section above it.
- **What did NOT change, verified before deployment (same discipline as Addendum 1):**
  every field `id` the JS reads is unchanged; `buildPayload()` and the omit-if-empty logic
  are untouched; `/score`, `/health`, `pipeline.py`, and `src/api/main.py`'s route are
  untouched. Checked again for duplicate element ids, balanced tags (div/section/form/
  header/footer/main/script/style/svg/details/select/label), and that every id referenced
  by the JS (all 16 form fields plus the 12 result-panel ids) is actually present in the
  markup, before pushing to the device.
- **Deployment note:** the first `device_commit_files` call for this version reported
  success (`written`, no `rejected` entries) but the device file's md5sum did not change --
  confirmed by re-checking immediately after. A second `device_commit_files` call with
  `force: true` against the same staged path did update it, verified by md5sum matching the
  staged file exactly. Recorded here in case this silent-no-op-on-first-attempt pattern
  recurs; the fix was simply to re-verify by md5sum after every device_commit_files call
  rather than trusting a "written" response alone, which is already this project's standing
  practice.
- **What I gave up:** nothing functional. Styling, copy, and attribution placement only.
- **Self-check:** *Why does giving the input fields a distinct tint instead of leaving them
  near-white actually fix a "theme mismatch" complaint, rather than just being a cosmetic
  preference -- what was the field doing before that made it look unrelated to the card
  around it?*

---

## 2026-10-08 — Stage 9, Part 3 design decisions: Tier 2 transfer (T1/T2/T3) and the
source-probe leakage test, logged before touching Tier 2 for evaluation purposes

Tier 2's 154 postings were already touched once, narrowly, in Stage 8b (3 postings pulled
by a mechanical rule for a qualitative demo — logged separately as not spending this
budget). This is the first time the FULL 154 are used for a quantitative result. Four
decisions, made before any of these four experiments ran.

### 1. T1 (temporal transfer): same 3-seed treatment as the main EMSCAD test result

- **Decision:** evaluate all 3 existing main-model checkpoints (seeds 0/1/2 — no
  retraining) on all 154 Tier 2 postings, report mean ± SD. Matches the treatment Stage 9
  Part 1 gave the main model and baselines on EMSCAD test (Decision 3, 2026-10-08) — the
  same parity reasoning applies: a 1-seed Tier 2 number next to a 3-seed EMSCAD number
  would make the EMSCAD side look more precise for no principled reason, and this is pure
  inference (cheap) so there's no GPU-budget reason to cut it to 1 seed the way the
  ablation arms were.
- **Self-check:** *Why is giving T1 three seeds the right call when the ablation arms
  (Decision 2026-10-06) were deliberately cut to one?*

### 2. T2 (signal durability): reuse the 5 ablation checkpoints already trained, no new
training

- **Decision:** run the 5 existing `models/stage9_ablation_{arm}_seed0.*` checkpoints
  (already trained for the EMSCAD-side ablation) on the same 154 Tier 2 postings, compare
  each arm's Δ-vs-full-model on Tier 2 to its Δ on EMSCAD test. This is what
  "ablation repeated on Tier 2" (methodology.md's T2 row) means in practice — the same 5
  trained models, a second evaluation set, not a second training run. Re-training 5 arms a
  second time (another ~2.25 hours) was never the plan and isn't needed: the question T2
  asks is whether a category's IMPORTANCE (measured by these same checkpoints) holds up on
  different-era data, not whether a Tier-2-trained model would ablate differently.
- **What this does NOT answer:** whether a model trained partly or wholly on Tier 2 would
  show a different category ranking — that's closer to T3's question, not T2's.
- **Self-check:** *Why does reusing the EMSCAD-trained ablation checkpoints on Tier 2
  still test "signal durability across eras," rather than just testing the same thing
  twice?*

### 3. T3 (domain adaptation): 50/50 stratified split, fine-tune 3 epochs, no held-out
Tier 2 validation set

- **Context:** 154 postings (24 fraud) is not enough to support a train/val/test split
  the way EMSCAD got one — any three-way split leaves too few fraud examples per portion
  to mean anything.
- **Decision:** one 50/50 split, stratified by `fraudulent` so both halves get a
  proportionate ~12 fraud postings, fixed seed. Continue training the frozen seed-0 EMSCAD
  checkpoint on one half for **3 epochs** (same batch size 16, same lr 2e-5 as every other
  fine-tuning run in this project — not re-tuned for this tiny dataset), evaluate once on
  the other half. The SAME frozen checkpoint is also evaluated zero-shot (no fine-tuning)
  on that same held-out half first, so the fine-tuned result has a same-data baseline to
  compare against, not just the EMSCAD-test number.
- **The epoch count is NOT validated against anything — this is a disclosed limitation,
  not an oversight.** There is no separate Tier 2 validation split to pick an epoch count
  against the way Stage 5's epoch count came from a real validation curve. 3 was chosen in
  advance as a small, conservative number (enough passes over ~77 rows to adapt without
  gross overfitting) and is reported as exactly that — a pre-committed guess, not a tuned
  hyperparameter. methodology.md states this plainly next to the T3 result.
- **What I gave up:** any claim that 3 epochs is the "right" amount of fine-tuning for
  this portion size. A different pre-committed number might show a different adaptation
  effect; this project reports what 3 epochs showed, not a sweep.
- **Self-check:** *Why is picking 3 epochs in advance and reporting it as unvalidated more
  defensible than trying several epoch counts and reporting whichever looked best?*

### 4. Source-probe leakage test: structured features only, EMSCAD-train vs. Tier 2-full,
class-weighted probe, ROC-AUC and balanced accuracy (not raw accuracy)

- **What "source" means here:** a binary label, EMSCAD vs. Tier 2 — exactly the
  "collection source" the guardrail and Decision 0.4 both name as the leakage risk to
  check (does the model, or a feature set like it, learn WHICH DATASET a posting came
  from rather than whether it's fraudulent).
- **Features:** the same 46 structured E1-E4 features the fraud model itself uses — not
  raw text. Text would trivially reveal source for an uninteresting reason (EMSCAD's
  text is anonymised with placeholder tokens; Tier 2's isn't) and wouldn't test what
  actually matters: whether the STRUCTURED FEATURES the model relies on encode source.
- **Data:** EMSCAD's TRAIN split (12,516 rows — test stays untouched) + all 154 Tier 2
  rows, combined. A stratified 80/20 split of this combined set (by source label, fixed
  seed) gives the probe its own train/test — the probe needs to generalise to unseen rows
  of each source just like any other classifier, not be graded on rows it was fit on.
- **Why NOT raw accuracy:** the combined set is ~98.8% EMSCAD / ~1.2% Tier 2 — a classifier
  that always predicts "EMSCAD" already scores ~98.8% accuracy while being completely
  uninformative about leakage. Reported as ROC-AUC (threshold-free) and balanced accuracy
  (mean of per-class recall) instead, with `class_weight="balanced"` on a LogisticRegression
  probe (same convention as the O2 baselines) so the probe isn't just learning to always
  guess the majority class.
- **Self-check:** *Why would reporting raw accuracy here make this leakage test actively
  misleading rather than just imprecise?*

---

## 2026-10-08 — Stage 9 design decisions, logged BEFORE touching the test split

Four decisions, all made and written down before any code reads `split == "test"` from
`data/interim/stage3_split.csv` — the point of writing this first is that none of it can
be revised once test results are visible, per the guardrail this project has repeated
since Day 1.

### 1. Evaluation thresholds stay `[TO SET]` — this does not block running Stage 9

- **Context:** the evaluation plan table (`methodology.md`) marks every success threshold
  `[TO SET]` and says plainly: "Thresholds must be agreed with supervisor BEFORE results
  are seen... now urgent." I have no record of supervisor contact happening this week.
- **Decision:** proceed with Stage 9 anyway. A threshold is only needed to answer "was
  this good enough" — it is not needed to compute Precision/Recall/F1/PR-AUC/ROC-AUC, the
  ablation deltas, or the Tier 2 transfer numbers themselves. Running Stage 9 now and
  deciding later whether the numbers clear some bar are two different acts; only the second
  one needs a threshold. The plan's own already-written fallback applies as-is: Chapter 5
  states plainly that thresholds were self-set under time pressure (if no supervisor
  contact happens before then), as a disclosed limitation, not a result presented as
  independently validated.
- **What I did NOT do:** invent a specific pass/fail number now and present it as agreed.
  That would be worse than leaving it open — a fabricated threshold is a threshold "set"
  with no one to set it against.
- **Self-check:** *Why is "no threshold yet" a reporting-honesty problem rather than a
  reason to delay running Stage 9 itself?*

### 2. All of Stage 9 — baselines, main model, ablation, Tier 2 — counts as ONE touch of
test, even though it runs as several separate script executions

- **Context:** the "test set used once" guardrail was already interpreted once, for the
  main 3-seed comparison ("3 model initialisations against one fixed split... the only
  reading compatible with the guardrail," 2026-09-20). Stage 9 adds more models that need
  to touch test: 2 baselines (now 3 seeds each, see Decision 3), the main model's existing
  3 seeds, and 5 ablation arms. That's 10 model configurations touching test, not 1.
- **Decision:** "used once" means the test labels are never used to make a further design,
  hyperparameter, threshold, or model-selection choice — not that literally one model may
  ever see them. Every one of these 10 configurations was pre-committed before Stage 9
  started (3 seeds: 2026-09-20; 5 ablation arms + `has_company_logo`: 2026-10-06). None of
  them is chosen, tuned, or swapped out *because of* what test shows. Running them together
  as one evaluation pass, across however many separate script invocations that practically
  takes, is the same act as running them in one process — no result is seen and acted on
  before the next one runs.
- **Hard constraint this creates going forward:** once ANY Stage 9 test number has been
  seen, no further change to the model architecture, feature set, seed choice, or ablation
  design is permitted for the rest of this project. Seeing a disappointing test F1 is not
  grounds to "try just one more thing" — that would retroactively break the very reading
  of "used once" this decision relies on.
- **Self-check:** *If the full model's test F1 turns out lower than its validation F1,
  what am I allowed to do about it, and what am I not allowed to do?*

### 3. Baseline models get the same 3-seed treatment as the main model for Stage 9,
closing an asymmetry `train_baseline.py` left behind

- **Context:** `train_baseline.py` fits LogReg/RF at all 3 seeds for its validation
  numbers, but only ever **saves seed 0's fit** to `models/` — seeds 1 and 2 were fit,
  measured, and discarded. The main DistilBERT model, by contrast, has all 3 seed
  checkpoints saved on disk. Evaluating Stage 9 as-is would give the main model mean±SD
  over 3 seeds on test, but baselines only a single seed-0 point value — a real asymmetry
  that would make the O2-vs-O3 test comparison look more precise for one arm than the
  other for no principled reason.
- **Decision:** before evaluating anything on test, refit baseline seeds 1 and 2 using the
  exact training code already in `train_baseline.py` (TRAIN split only, identical
  TF-IDF/LogReg/RF settings, seeds 0/1/2) — this does not touch test, it only reproduces
  work already specified and already done once at validation time, just without discarding
  the fitted models this time. All 3 seeds of both baselines are then evaluated on test
  once, mean±SD, matching the main model's treatment exactly. Cost: ~30 seconds total
  (LogReg ~8s + RF ~4s, per seed, per the Stage 5 timing already measured) — cheap because
  these are the same fast sklearn models, not DistilBERT fine-tuning.
- **What I gave up:** nothing material — this is strictly more rigorous than the
  alternative (disclosing the asymmetry and reporting baselines as single-point), at
  near-zero cost.
- **Self-check:** *Why does refitting baseline seeds 1/2 on train-only data NOT count as
  "touching test more than once," even though it happens inside the Stage 9 script that
  also evaluates on test?*

### 4. Ablation arms are compared against the full model's seed-0 test result, not the
3-seed mean

- **Context:** the ablation (5 arms, 1 seed each — closed 2026-10-06) needs a Δ F1 / Δ
  PR-AUC baseline to subtract from. The full model has 3 seeds on test; the ablation arms
  have 1 each.
- **Decision:** compare each 1-seed ablation arm against the full model's **seed-0** test
  result specifically (the same seed, same initialisation convention used throughout this
  project as "the" reference model), not the 3-seed mean. This keeps the comparison to a
  single run-to-run noise profile on both sides rather than mixing a single noisy
  measurement against an averaged one. The 3-seed mean is still reported separately as the
  headline O3 result; the ablation table is explicitly a seed-0-vs-seed-0 comparison, and
  methodology.md will say so.
- **What I gave up:** an ablation Δ that's exactly comparable to the headline mean±SD
  number — it isn't, and the writeup will say which baseline number the ablation actually
  used, rather than letting a reader assume it was the mean.
- **Self-check:** *Why would comparing a 1-seed ablation result to the full model's 3-seed
  mean (instead of seed 0 specifically) risk crediting or blaming a category for what is
  actually just seed-to-seed noise?*

---

## 2026-10-08 — Stage 8b executed: near-identical explanations for the two BBB-sourced
examples, confirmed as the Decision 0.4 field asymmetry, not a bug

- **What happened:** `stage8b_select.py` ran clean (154/154 Tier 2 postings scored,
  3 selected by the pre-registered rule above). But `clear_fraud` (fraud#10) and
  `ambiguous` (fraud#20) — both drawn from BBB Scam Tracker — came back with **word-for-
  word identical `top_reasons`**, and both showed **`suspicious_phrases: []`** despite
  being confirmed real scams. Before writing either into methodology.md I checked both
  against the raw source data rather than assuming either was a defect.

- **Finding 1 — identical top_reasons, verified cause:** I read the raw JSONL records for
  both postings directly (`data/raw/tier2/tier2_fraud_raw.jsonl`, index 10 and 20). Every
  single structured field — title, location, department, salary_range, employment_type,
  required_experience, required_education, industry, function, company_profile,
  telecommuting, has_company_logo, has_questions — is `None` on **both** records; they
  differ only in free-text description. Stage 7's SHAP design (logged already) deliberately
  scopes explanation to the 46 structured E1-E4 features and holds DistilBERT's [CLS] text
  embedding fixed, unexplained. Two postings with identical (all-null) structured vectors
  therefore produce near-identical structured-feature SHAP rankings by construction, even
  though their actual scores differ (7 vs. 25) because that difference is driven entirely by
  DistilBERT's reading of the different description text — a channel this explanation
  pathway doesn't expose. This is the SAME field-asymmetry property already logged in
  Decision 0.4 ("Tier 2 field symmetry... BBB Scam Tracker reports document almost no
  structured fields"); Stage 8b's live output is the first place it was actually seen to
  bite, not a new problem.

- **Finding 2 — `suspicious_phrases: []`, verified not a bug:** I pulled both description
  texts and checked them against every compiled pattern in `E1_LEXICON`
  (`src/features/extract_features.py`) directly — zero matches on either text, confirmed by
  running the actual compiled regex groups against the actual text, not by inspection. The
  lexicon targets "classic" scam-ad phrasing (guaranteed income, wire transfer, act now);
  these two BBB reports are written in a more modern, narrative, first-person-victim-report
  style that doesn't use that phrasing. The full fused model still flagged both with high
  confidence (93%, 75% calibrated P(fraud)) through other signals — text embedding +
  structural completeness — which is a point *for* the multi-signal design over a
  lexicon-only approach, not evidence against it, but it does mean E1's contribution to
  these two particular explanations is honestly zero, and methodology.md's Stage 8b table
  says so rather than hiding it.

- **Finding 3 — `ambiguous`'s calibrated P(fraud)=0.75 is not a literal coin-flip:** by
  construction, `ambiguous` is the Tier 2 posting whose calibrated P(fraud) is closest to
  0.50 among all 154 — that is guaranteed by the selection code, not something I needed to
  re-verify. But 0.75 is not close to 0.50 in any absolute sense. I have NOT re-run all 154
  scores to inspect the full distribution (would need the student's torch-enabled venv, not
  available to me directly), so I can't measure how skewed it is — I can only report what
  the selection already proved: 0.75 was the single closest value available across all 154,
  meaning the model essentially never expressed genuine 50/50 uncertainty on this Tier 2
  sample. A plausible explanation is the sigmoid-saturation/skew behaviour already documented
  in Stage 7, but that is an unverified inference, flagged as such, not a measured fact —
  Stage 9's full Tier 2 run will show the actual probability distribution.

- **Why none of this was fixed:** all three are properties of the data and the already-
  agreed SHAP scope, not implementation defects — there is nothing here that a code fix
  closes without reopening Decision 0.4 or Stage 7's SHAP-scope decision, which were each
  already made deliberately and for stated reasons. Re-opening them now, after seeing this
  one demo's output, would itself violate "a threshold set after seeing results is not a
  threshold" by a different name.

- **What I gave up:** a cleaner-looking three-example table. The honest version says plainly
  that two of the three explanations look alike and that neither flags a lexicon phrase, and
  explains why, rather than quietly presenting only the parts that look good.

- **Self-check:** *Why does "the two explanations are nearly identical" not contradict
  "the model scored them differently and correctly," and what would have to be true about
  SHAP's scope for that not to happen?*

---

## 2026-10-08 — Stage 8b selection method: how to pick 3 "real" postings without cherry-picking

- **Context:** PROJECT_PLAN.md commits to Stage 8b running "3 real postings through the live
  API — clear fraud, clear legit, one genuinely ambiguous. No cherry-picking." That commitment
  is empty without a pre-specified rule for what "clear" and "ambiguous" mean — otherwise
  "no cherry-picking" just means I don't LOOK like I picked favourably, while still reading
  posting text and choosing whichever three tell the best story. Decided and logged here
  BEFORE running the selection script or looking at any individual posting's output.

- **Source:** Tier 2 (`data/raw/tier2/tier2_fraud_raw.jsonl` + `tier2_legit_raw.jsonl`, 24 +
  130 = 154 real postings), not EMSCAD's test split. Two reasons: (1) EMSCAD test is
  untouched until Stage 9's one-time evaluation — using even 3 test rows here would spend
  that guardrail before Stage 9 runs, for a demonstration that doesn't need it; (2) Tier 2 is
  genuinely external, contemporary, real-world data, never used for training — closer to what
  "a real job seeker pastes a real posting" actually means than a 2012-2014 EMSCAD row would
  be. Stage 9 still runs the FULL 154-posting Tier 2 set for its own quantitative temporal-
  transfer result later — pulling 3 out now for a qualitative demo doesn't spend or bias that
  (FEDS positioning already distinguishes demonstration, "does it work at all," from
  evaluation, "how well" — different stages, different purposes).

- **Selection rule (mechanical, blind to posting content):**
  1. Score all 154 Tier 2 postings through the real, frozen pipeline (score only — SHAP
     explanation computed only for the 3 finally selected, not all 154).
  2. **Clear fraud** = the TRUE-fraud posting with the HIGHEST calibrated P(fraud) — the
     model's own most confident correct fraud call.
  3. **Clear legit** = the TRUE-legit posting with the LOWEST calibrated P(fraud) — the
     model's own most confident correct legit call.
  4. **Ambiguous** = the posting (either true label) with calibrated P(fraud) closest to
     0.50 — genuine model uncertainty, not my subjective read of how convincing the text is.

- **Options considered:** (A) read through Tier 2 myself and pick 3 examples that illustrate
  the framework well; (B) the mechanical rule above, applied to the model's own output;
  (C) random selection (one random true-fraud, one random true-legit, one random overall).
- **Why B:** option A is cherry-picking with extra steps — "no cherry-picking" has to mean
  the SELECTION PROCEDURE can't see posting content before committing to which ones get used,
  not just that I don't admit to liking the examples. Option C is honestly non-cherry-picked
  too, but a random "ambiguous" pick could easily land on a posting the model is actually
  quite confident about by chance (with only 154 postings, a uniform random draw isn't
  guaranteed to land anywhere near the 0.5 boundary) — which would undercut exactly the point
  Framework_Explanation_Walkthrough.docx makes about why the ambiguous case matters ("shows
  how the framework behaves in the middle of the distribution"). Option B gets genuine
  ambiguity by construction while staying just as blind to content as random selection.
- **What I gave up:** the chance to hand-pick a posting that makes for the cleanest possible
  demo narrative. That is precisely the cost "no cherry-picking" is supposed to impose.
- **Self-check:** *Why does picking posting content myself still count as "cherry-picking"
  even if I only look at the MODEL'S output and not the text, and why does random selection
  not fully solve the "genuine ambiguity" requirement the way the closest-to-0.5 rule does?*

---

## 2026-10-08 — Stage 8 smoke test caught an inverted credibility score (direction bug, not a Stage 8-only bug — traced to calibrate.py's own framing)

- **What happened:** the first real end-to-end run of the wired API (`stage8_smoke_test.py`)
  scored an obviously fraudulent posting (urgent hiring, guaranteed $500/day, registration
  fee, "contact us at our personal email", act-now pressure) at **71/100, "Low risk"**, and
  scored a clean, complete, ordinary posting at **2/100, "High risk"** — exactly backwards.

- **Root cause:** the DistilBERT+evidence model is trained on `y = train["fraudulent"]`
  (`train_distilbert.py`), so its raw and calibrated output is **P(fraudulent=1)**, not
  P(credible). `calibrate.py`'s own docstring states "the 0-100 `credibility_score` Stage
  8's API returns is this calibrated probability x 100" and its code computes
  `scores_0_100 = final_prob * 100` directly — treating calibrated P(fraud) as if it were
  already a credibility score. Confirmation this was wrong, not a one-off: the file's own
  `calibrated_score_summary.mean` is **4.85 on validation**, matching the ~4.8% fraud base
  rate almost exactly — i.e. it is unambiguously the mean of calibrated P(fraud), not
  P(credible) (whose mean should sit near 95.2, not 4.85). I built Stage 8 against this
  existing convention without re-deriving it from the training label, and carried the same
  inversion into `pipeline.py`'s `run_inference()` — and, separately, into
  `_describe_feature()`'s "raised/lowered the score" wording, since SHAP there explains the
  same fraud-direction logit (Stage 7's own convention; correct for Stage 7's purposes,
  which never relabels it as "credibility").

- **What is NOT affected:** the calibration science itself. Brier/ECE, which calibrator won
  (isotonic), the reliability curve, and Stage 7's entire SHAP/fidelity analysis are all
  computed against the `fraudulent` label consistently and remain correct — only the final
  semantic label attached to the 0-100 number ("credibility" vs. "fraud risk") was backwards.
  This is contained to: (1) `calibrate.py`'s docstring/variable naming (not fixed — see
  below), (2) one sentence in `methodology.md`'s Calibration section (fixed, see that file),
  (3) `src/api/pipeline.py` (fixed, this entry), (4) a standing warning for whoever writes
  Stage 9's final results, so the same inversion isn't re-introduced there.

- **Fix (`src/api/pipeline.py`, `run_inference`):** the model/calibrator's output is now
  explicitly named `calibrated_fraud_prob` (not `calibrated_prob`), and
  `credibility_prob = 1.0 - calibrated_fraud_prob` is computed as its own step before
  `score = round(credibility_prob * 100)`. `_describe_feature()`'s direction logic flipped
  to match (`direction = "lowered" if shap_value > 0 else "raised"`, since a feature that
  pushes the logit up pushes P(fraud) up, which lowers credibility). `risk_band_from_score()`
  itself needed NO change — it was already written correctly (low score -> High risk, per
  Finding 1 earlier today); it was simply being fed an already-inverted score.

- **`calibrate.py` itself deliberately left unchanged:** its stored numbers
  (`calibrated_score_summary`, Brier, ECE, the selected calibrator) are all still accurate
  descriptions of calibrated P(fraud) — re-running Stage 6 would not change any of them.
  Only the English label "credibility_score" attached to that number, in the docstring and
  in methodology.md, was wrong. Fixing the docstring there is low-risk housekeeping, not
  logged as a separate decision; the methodology.md sentence is corrected directly (see
  that file's Calibration section) since that one DOES claim a specific interpretation in a
  document that will be read standalone.

- **Why this matters beyond Stage 8:** if this had gone uncaught until Stage 9 (which
  reports the final, citable test-set numbers) or into Chapter 4's write-up, "credibility
  score" would have been reported backwards in the dissertation's headline result — a
  Discussion-chapter-breaking error, not a cosmetic one. Caught here specifically because
  Stage 8's smoke test ran two hand-picked, obviously-labelled examples (one clearly
  fraudulent, one clearly ordinary) BEFORE Stage 8b's formal demonstration and well before
  Stage 9 — exactly what hand-picked smoke-test examples are for.

- **Also fixed in the same review pass (templating bug, not another direction inversion):**
  `_describe_feature()`'s `E1_phrase_*` and `E2_location_specificity` branches always said
  a phrase "was found" / named an active category, without checking whether the feature's
  value was actually 1 — harmless in this run (the phrases it named for the "suspicious"
  smoke-test example genuinely were present) but a latent correctness bug: if SHAP ever
  ranks a feature's ABSENCE as important, the old text would have falsely claimed something
  was found that wasn't. Both branches now check `value >= 0.5` the same way the
  `E3_*_present` / `E2_company_profile_present` branches already did correctly.

- **A genuine (non-bug) finding from the same smoke-test run, worth knowing before Stage 8b
  or a viva:** for the "suspicious" example, 2 of the top-5 SHAP reasons showed a scam-style
  phrase group (`off_platform_contact`, and the overall `E1_suspicious_phrase_count`)
  RAISING credibility rather than lowering it, while the model's overall verdict (29/100,
  correctly "High risk") was still right. Not re-litigated or "corrected" here — overriding
  individual SHAP signs to match intuition would fabricate agreement between the explanation
  and a prior belief, exactly what Stage 7's fidelity testing exists to check for
  objectively rather than assume. Plausible (not verified) explanation: `train_distilbert.py`
  already documents that E1 features are REDUNDANT with the raw text DistilBERT reads
  directly (its own [CLS] embedding is held fixed; only the structured E1 flag is toggled),
  and a redundant feature's own head-weight can be locally noisy/counter-signed for a
  specific instance without damaging the model's overall accuracy or Stage 7's
  aggregate SHAP-vs-random fidelity result. Only two hand-picked examples were run — this is
  an observation to keep in mind, not a measured, general claim. Worth a sentence in Chapter
  5 if this exact example or anything like it is used in Stage 8b's demonstration.

- **Self-check:** *Why does "mean calibrated score = 4.85, matching the fraud base rate"
  prove the number is P(fraud), not P(credible) — and why did Stage 7's SHAP/fidelity
  results not need any correction even though they use the exact same model output?*

---

## 2026-10-08 — Stage 8 wiring: API input contract resolved (schema expanded, not text-only); two deployment-time findings caught before shipping

- **Context:** starting Stage 8 (replacing the four stub functions in `src/api/main.py`), I
  read Stage 4's real code (`extract_features.py`) against the API contract and found the
  project's own files disagreed. `schemas.py` / `PROJECT_PLAN.md` / `project.md` describe
  `/score`'s input as raw text (primary) or a URL (secondary) only. But the already-finalized
  `Framework_Explanation_Walkthrough.docx` (Step 1) says "the primary input path is raw
  posting text **with any structured fields the caller can supply**." `extract_all()` needs
  15 EMSCAD-shaped columns to do E2/E3/E4 at all — most of them (`salary_range`,
  `employment_type`, `required_experience`, `required_education`, `department`, `industry`,
  `function`, `has_company_logo`, `has_questions`) are platform metadata, not something
  recoverable by parsing pasted prose. A text-only contract would make E3/E4 — the project's
  actual contribution — permanently dark on every live request.

### Decision 1 — expand `ScoreRequest`, don't keep it text-only

- **Options considered:** (A) expand `ScoreRequest` with the ~10 structured fields as
  optional inputs, matching the walkthrough doc; (B) keep text-only, every structured field
  permanently missing at inference time; (C) keep text-only, but heuristically split the
  pasted blob into title/requirements/benefits sections to recover some fields.
- **Why A:** reuses `extract_features.py`'s existing missingness semantics completely
  unchanged — an unsupplied field at inference time is handled by exactly the same code path
  as a missing field in EMSCAD, not a new behaviour. Keeps E3/E4 meaningfully alive for real
  queries, including Stage 8b's planned "ambiguous case" demonstration, which per the
  walkthrough doc depends on at least one structured-field-vs-text contradiction actually
  being checkable. Resolves the inconsistency in favour of the document that was already
  finalized and specific, rather than the shorter PROJECT_PLAN.md/project.md bullets, which
  read as an abbreviation that drifted, not a deliberate redesign. Option C was rejected
  specifically: splitting a text blob into EMSCAD-shaped sections is an untested, unvalidated
  heuristic the model was never trained or tested against — it would silently create a
  train/inference mismatch worse than honestly leaving a field missing.
- **What I gave up:** PROJECT_PLAN.md's and project.md's one-line "Input" descriptions needed
  a one-line correction (not a redesign) to match what the walkthrough doc already committed
  to. A slightly more complex request schema than the original "just paste some text" pitch.
- **Delegated:** I raised this as a blocking question before writing any Stage 8 code; the
  answer was to use my own judgement given full authority, so this decision is mine to defend
  in a viva, not a student-made call relayed here.
- **Self-check:** *Why is heuristically splitting pasted text into EMSCAD-shaped sections
  (option C) worse than just leaving the unsupplied structured fields genuinely missing?*

### Finding 1 — `calibrate.py`'s `risk_bands_0_100` dict keys name the SCORE band, not the risk level

- **What I found:** `models/stage6_calibrator.joblib` / `reports/stage6_calibration_results.json`
  store `risk_bands_0_100 = {"low": [0,33], "medium": [34,66], "high": [67,100]}`. Read
  naively, a score of 10 would map to `risk_band="Low"` — but `credibility_score` is defined
  (schemas.py) as "higher = more credible," so a score of 10 is the HIGH-risk end, not low.
  The dict's own key names describe the position of the score band, not the direction of risk.
- **Fix:** `src/api/pipeline.py`'s `risk_band_from_score()` uses the same two thresholds
  (33/66, the real Stage-6-measured terciles) but maps them score-low→`"High"`,
  score-mid→`"Medium"`, score-high→`"Low"` — the inverse of `calibrate.py`'s own key labels.
  Confirmed against the one place project documentation states the intended direction
  explicitly (`Framework_Explanation_Walkthrough.docx`, "0–39 High risk ... 70–100 Low") —
  only the DIRECTION is taken from that doc, never its specific numbers (guardrail: that
  file's numbers are an illustrative worked example, never citable — see sources.md #17).
  The actual thresholds used are Stage 6's own measured terciles.
- **Not revisited in `calibrate.py` itself** — renaming its dict keys is a harmless cosmetic
  fix but touches an already-reported Stage 6 results file; left as-is with this note, since
  Stage 8 is the only consumer and now handles the direction correctly.

### Finding 2 — E2's contact-token features are structurally inert on real deployment text

- **What I found:** Stage 1's `extract_contact_tokens()` (and therefore `E2_url_token_count`
  / `E2_email_token_count` / `E2_phone_token_count`) matches EMSCAD's specific anonymisation
  placeholder format (`#EMAIL_[hex]#`, etc.) — not a real email address, phone number, or
  URL. EMSCAD's own description text already has these baked in (the dataset's own
  anonymisation leaves hashed tokens in place of real contact details). A real job seeker
  pasting a real posting will never produce that literal token format, so these three
  features will read 0 for every live API request, regardless of whether the posting
  actually pushes off-platform contact.
- **Decision:** not fixed now. Building a second, live-text contact-detector (real email/
  phone/URL regexes) would be new scope the student hasn't signed off on, not a Stage 8
  wiring task, and risks silently changing what the trained model's E2 features mean versus
  what was measured and reported in Stage 9. Logged here as a disclosed, known deployment
  characteristic — worth a sentence in Chapter 6 limitations — not silently left unmentioned.
- **Revisit if:** the student wants a live-text contact-pressure signal added to the API
  response (e.g. for `verification_checklist`) as separate, clearly-labelled, non-trained
  logic — never folded back into the E2 feature vector the trained model actually consumes.
- **Self-check:** *Why can't `E2_*_token_count` detect a real email address pasted into a
  live `/score` request, and why is "fix it now" the wrong move for Stage 8?*

---

## 2026-10-08 — Stage 7 complete: logit-space fidelity run gives a real, consistent SHAP-vs-random gap; rule-consistency caveat strengthened by what the re-run showed

- **Results (seed-0 model, 260 validation postings, logit-space, 26.9s total runtime):**

  | k | SHAP comp. | Random comp. | Gap | SHAP \|suff.\| | Random \|suff.\| |
  |---|---|---|---|---|---|
  | 2 | 0.0390 | 0.0023 | +0.0367 | 0.0388 | 0.0660 |
  | 5 | 0.0457 | 0.0055 | +0.0402 | 0.0203 | 0.0615 |
  | 10 | 0.0451 | 0.0106 | +0.0345 | 0.0110 | 0.0541 |
  | 15 | 0.0417 | 0.0149 | +0.0267 | 0.0079 | 0.0464 |
  | 23 | 0.0430 | 0.0231 | +0.0199 | 0.0022 | 0.0346 |

  Unlike the probability-space run, this gap is large relative to the random control at
  every k (SHAP's comprehensiveness is 4-17x random's), not just positive. The logit-space
  switch (previous entry) is confirmed to have been the right call, not just a plausible
  theory.
- **Rule-consistency: 100% (14/14), 95% Wilson CI [0.785, 1.000] — identical at top-5,
  top-10, AND top-15.** This is new information the re-run surfaced: a fired rule's feature
  isn't just somewhere in a generous top-15 cutoff, it's inside the top-5 of 46 features
  every single time. That strengthens, not weakens, the limitation already logged in the
  previous entry: this pattern is exactly what the "sparse feature far from its background
  value gets a structurally large SHAP attribution" explanation predicts, regardless of
  whether the model substantively relies on the rule. I'm not walking back the finding —
  the gap evidence above is separately real — but methodology.md's writeup states this
  caveat directly next to the 100% figure, not as a buried footnote, specifically because
  the re-run made the pattern more pronounced, not less.
- **A real bug caught on the first logit-space attempt, before any number was trusted:**
  the run crashed during `json.dump` with `TypeError: Object of type float32 is not JSON
  serializable` — AFTER all 260 postings' SHAP computation had already finished correctly
  (confirmed by the printed per-posting progress and timing). One display-only value
  (`orig_probs[i]`, indexed directly from a `float32` numpy array) was being written into
  the results dict without an explicit `float()` cast; `numpy.float32` doesn't subclass
  Python's `float` the way `numpy.float64` does, so the standard library's `json` module
  rejects it. One-line fix (`float(orig_probs[i])`), verified with a standalone
  `json.dumps` test against the actual nested structure before pushing, then confirmed by
  the successful second run. Logged because it's a genuine, specific bug — not because a
  trivial fix needs a full decision entry on its own, but so the pattern ("numpy scalars
  silently work everywhere except `json.dump`") is on record if it recurs elsewhere (Stage
  9's result-writing code should be checked for the same thing before it runs).
- **Stage 7 status:** complete. `methodology.md`'s "Explanation fidelity (O4)" section and
  `PROJECT_PLAN.md`'s Stage 7 checklist (both the narrative Day-4 line and the §7.5 live
  checklist) are updated with these real numbers.
- **Self-check:** *Why does the rule-consistency result being identical at top-5 and
  top-15 make the sparse-feature-inflation caveat MORE important to state, not less — and
  why doesn't that undercut the separate comprehensiveness/sufficiency finding, which uses
  a completely different mechanism (deletion/insertion, not ranking position)?*


---

## 2026-10-08 — Stage 7 first real run flagged a measurement problem: switched SHAP/fidelity from probability space to logit space

- **Context:** The first real `src.explain.shap_explain` run (260 postings, probability
  space, the original default) completed cleanly and printed a SHAP-vs-random gap that
  was positive at every k — a real signal — but tiny: comprehensiveness ranged
  0.0015-0.0023, sufficiency |diff| 0.0001-0.0016. Numbers this small are not a citable
  fidelity result on their own; before writing them into `methodology.md` I looked at why
  they were this small rather than reporting them as-is.
- **What's actually going on:** this model's raw probability output is skewed low
  (consistent with Stage 6's calibrated-score mean of 4.8/100 on validation) — most
  sampled postings' predicted probability sits in the flat part of the sigmoid, where its
  derivative is close to zero. In that region, masking even a genuinely important feature
  barely moves the OUTPUT PROBABILITY, regardless of whether the SHAP ranking is faithful.
  The compression is a property of the probability transform at this operating point, not
  evidence the explanations are weak.
- **Decision:** `src/explain/shap_explain.py` now explains and fidelity-tests the model's
  raw LOGIT (pre-sigmoid score) by default (`--output-space logit`), not the post-sigmoid
  probability. `--output-space prob` is kept as an explicit option so the original,
  saturated numbers can still be shown for comparison if useful in the write-up, rather
  than silently discarded.
- **Is this "a threshold set after seeing results"?** No — that guardrail is about moving
  the bar for what counts as a good result after seeing how a fixed method scored. Here
  the bar is unchanged (SHAP's ranking must still beat a random one); what changed is the
  SCALE the comparison is measured on, because the original scale was discovered to
  mechanically compress the true effect size for this specific model's output
  distribution. This is the same category of catch as the Stage 5 checkpoint-filename bug
  or the Stage 6 isotonic-overfitting caveat: a flaw in the MEASUREMENT, found and fixed
  before being written up, not a result that was massaged to look better.
- **What I gave up:** nothing in rigor — logit-space attributions are the more standard
  choice for SHAP on a classifier head precisely because they avoid this saturation issue;
  if anything this is the more defensible default, not a compromise.
- **Other corrections made at the same time (same run, no extra cost):** rule-consistency
  is now reported as a sensitivity sweep across top-{5,10,15} features, each with a Wilson
  95% confidence interval, instead of one bare top-10 mean — the first run's
  "rule-consistency = 1.0000" came from only 14 postings with a fired rule, and a perfect
  score from n=14 is weaker evidence than "1.0000" looks; the CI makes that explicit
  (Wilson lower bound ≈0.78, not 1.0). Also noted as a limitation: sparse binary features
  that are almost always 0 sit far from the background/mean value whenever they DO fire,
  which structurally tends to earn them large SHAP attributions on its own — so a high
  rule-consistency figure is consistent with, but doesn't on its own prove, the model
  genuinely relying on that rule rather than just reacting to any rare deviation. The
  discussion chapter should carry this caveat rather than present rule-consistency as an
  unqualified finding.
- **Self-check:** *Why does fixing the output space after seeing the first run not count
  as the same mistake as setting a decision threshold after seeing results — what's the
  actual difference between "the bar moved" and "the ruler was broken"?*

---

## 2026-10-08 — Stage 7 explainability built: validation (not test) for fidelity testing, SHAP scoped to the 46 structured features, sample oversamples fraud

- **Context:** `PROJECT_PLAN.md`'s Day-4 plan text said "consider sub-sampling the test
  set for the fidelity tests specifically... log this as a decision if you do it, don't
  let it happen silently." Building `src/explain/shap_explain.py` meant settling that,
  plus three implementation choices, before any GPU time was spent.

- **Decision 1 — validation, not test, for Stage 7's fidelity sample.**
  - **Options considered:** (A) sub-sample the test set, as the plan text suggested;
    (B) use validation instead.
  - **Why (B):** Comprehensiveness, sufficiency, and rule-consistency only ever consume
    the model's OWN predicted probability and a posting's OWN C1-C6 flags — no true label
    enters the masking/ranking math anywhere, so a strict reading of "test used once"
    (which exists to stop a test LABEL influencing a decision) could arguably permit (A).
    But resting an interpretation of the project's single strongest, explicitly
    never-cut guardrail on that distinction isn't worth the risk under deadline pressure —
    the guardrail's whole point is to remove ambiguity about whether test was "really"
    touched. Validation gives identical fidelity evidence with zero exposure to that
    argument being challenged in a viva.
  - **What I gave up:** nothing measurable — the fidelity tests don't care which split's
    postings they run on, as long as the model wasn't fit on them, and both qualify.
  - **Self-check:** *Why would sub-sampling test for comprehensiveness/sufficiency not
    actually violate "test used once" as that guardrail is meant to protect against — and
    why did I avoid relying on that argument anyway?*

- **Decision 2 — SHAP scoped to the 46 structured E1-E4 features, not raw tokens;
  DistilBERT's [CLS] embedding computed once per posting and reused across all SHAP
  coalitions.**
  - **Options considered:** (A) token-level SHAP over DistilBERT's full input (needs
    roughly one full transformer forward pass per SHAP coalition sample, per posting);
    (B) KernelExplainer over only the structured feature vector, holding the posting's own
    [CLS] embedding fixed and varying only structured features through the cheap MLP head
    (`FusedModel.head`).
  - **Why (B):** This project's explainability contribution is the E1-E4 evidence
    taxonomy, not token attribution — (B) explains exactly that, at the same feature
    granularity Stage 9's ablation already uses (so SHAP values can be summed per group —
    E1/E2/E3/E4 — and compared against ablation's per-group delta-F1 later, if useful for
    Chapter 4/5, without re-running SHAP). It is also the only option that fits Day 4's
    budget: (A) costs (nsamples x postings) full BERT forward passes; (B) costs exactly one
    BERT forward pass per posting, full stop.
  - **What I gave up:** an explanation of DistilBERT's own token-level attention — out of
    scope for O4, and already an accepted cost of dropping LIME for SHAP alone (see
    "Explainability: SHAP only, LIME dropped," 2026-09-20).
  - **Self-check:** *Why doesn't fixing the [CLS] embedding and only varying the 46
    structured features through the model's head, rather than the whole model, make the
    resulting SHAP values "less real"? What is actually being explained here?*

- **Decision 3 — sample composition: all validation fraud (~130 rows) plus an
  equal-sized random sample of validation legit, not a plain random sample of validation.**
  - **Options considered:** (A) a plain random sample of validation (would carry only
    ~10-12 fraud rows at the true 4.8% base rate — too few for a stable per-rule or
    per-class fidelity estimate); (B) all fraud + matched random legit.
  - **Why (B):** The fidelity tests and rule-consistency check are statistics ABOUT the
    explanations, not a prevalence estimate — there is no guardrail reason to preserve the
    4.8% base rate here the way Stage 9's one-time test evaluation must.
  - **What I gave up:** the ability to quote a single "X% of postings have
    rule-consistency Y" figure at the true base rate. Results here are conditional,
    reported by class where it matters, and the output JSON carries an explicit
    "not prevalence-representative" note so this can't later be misquoted as a population
    estimate.
  - **Self-check:** *Why is deliberately oversampling fraud for THIS stage not the same
    mistake the "never present a cherry-picked best case as typical" guardrail warns
    against?*

- **Implementation notes (logged for completeness, not separately viva-worthy):**
  KernelExplainer's background and the comprehensiveness/sufficiency deletion/insertion
  masking both use the SAME reference vector — the saved `StandardScaler`'s `mean_` (the
  TRAIN set's per-feature mean, raw units) — so SHAP's notion of "missing" and the
  fidelity tests' notion of "removed" are one operation, not two conventions that happen
  to share a name. `l1_reg=0` is passed to `shap.KernelExplainer.shap_values` so all 46
  features get an attribution, instead of KernelExplainer's default sparsifying feature
  selection silently zeroing some out. Fidelity is reported as a GAP against a
  random-ranking control averaged over 10 reps per posting — the gap, not SHAP's number in
  isolation, is the actual fidelity evidence; if the gap is small or negative, that is the
  honest result, not a sign something needs re-running until it looks better.
  `src/explain/shap_explain.py` was built and smoke-tested (pure-function logic plus a
  real `shap.KernelExplainer` call against a synthetic model, mirroring the
  smoke-testing discipline used for `train_distilbert.py` and `calibrate.py`) before
  the first real run. That first run (probability space) is what surfaced the
  saturation problem described in the entry directly above this one — real results are
  there, not here.

---

## 2026-10-08 — Stage 6 complete: isotonic selected over Platt, with an honest caveat about what its ECE=0.000 actually means

- **Results on validation (seed-0 DistilBERT+evidence model, n=2682):**

  | Calibrator | Brier | ECE |
  |---|---|---|
  | None (raw) | 0.0275 | 0.0231 |
  | Platt | 0.0212 | 0.0050 |
  | Isotonic | 0.0199 | ~0.0000 |

  No disagreement between the two metrics — isotonic wins on both, cleanly. The reliability
  curve shows the raw model is genuinely overconfident (predictions sit below the diagonal
  through the mid-range, then jump sharply only in the 0.9–1.0 bin), and both calibrators
  visibly correct it.
- **Decision:** isotonic selected, saved to `models/stage6_calibrator.joblib`.
- **The caveat, stated plainly:** isotonic's near-zero ECE is partly an artefact of fitting
  and evaluating on the SAME validation set. Isotonic regression is a flexible, non-
  parametric, many-degrees-of-freedom fit — several of its reliability bins show mean
  confidence matching the actual fraction positive to 3+ decimal places, which is exactly
  what you'd expect from a method with enough flexibility to closely trace its own
  training sample's empirical curve. Platt (a single-parameter logistic fit) has much less
  room to do this, which is part of why its ECE (0.005) is non-zero but still good. This
  does not mean isotonic was the wrong pick — it won on Brier too, a different and less
  gameable metric, so the preference is real, not just an artefact. But the exact ECE=0.000
  number should not be quoted as the model's true calibration error; it is a validation-set
  selection statistic, not the final answer.
- **Why this isn't a problem for the project's "test used once" guardrail:** this is
  precisely the situation that guardrail exists for. The calibrator was chosen here, on
  validation, exactly once. Stage 9's one-time test-set evaluation applies this same frozen
  isotonic calibrator (not re-selected, not re-fit) and reports ITS Brier/ECE — that number,
  not this one, is what Chapter 4 should present as the real calibration result.
- **Risk bands:** provisional terciles (Low 0–33, Medium 34–66, High 67–100) on the
  calibrated 0–100 score. Not validated against any external standard — logged as such
  because `PROJECT_PLAN.md` already records success thresholds as open pending supervisor
  input. Revisit if a supervisor contact window opens.
- **What I gave up:** a clean, uncomplicated "ECE went from 0.023 to 0.000" headline
  number. Reporting the honest version (real but likely overstated at exactly 0, confirm
  on test) costs a cleaner story in exchange for not overclaiming in Chapter 4.
- **Self-check:** *Why can isotonic regression report a near-perfect ECE on the same data
  it was fit on, when Platt scaling can't do the same thing nearly as easily — and what
  does that imply about which number you trust more going into Stage 9?*

---

## 2026-10-08 — Stage 5 main comparison complete: DistilBERT + structured evidence beats both baselines; ablation seed count (Decision 2, 2026-10-06) closed at 1 seed, from measured timing

### 1. Main comparison result (O3)

3 seeds (0/1/2), 5 epochs each (the measured peak — see the epoch-count entry above),
identical validation split, `pos_weight` class imbalance handling:

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| TF-IDF + LogReg (baseline) | 0.464 | 0.692 | 0.556 | 0.655 | 0.931 |
| TF-IDF + RF (baseline) | 0.881 | 0.362 | 0.513 | 0.682 | 0.940 |
| DistilBERT + structured evidence | 0.634 ± 0.050 | 0.713 ± 0.004 | **0.671 ± 0.030** | 0.710 ± 0.018 | 0.934 ± 0.008 |

F1 improves over both baselines (Δ +0.115 vs. LogReg, +0.158 vs. RF), with a precision/
recall balance that sits between the two baselines rather than reproducing either one's
extreme trade-off (LogReg: high recall/low precision; RF: high precision/low recall).
ROC-AUC is roughly level with both baselines (0.934 vs. 0.931/0.940) — the gain is
concentrated in F1/PR-AUC, not ROC-AUC, worth noting honestly in Chapter 4 rather than
implying a uniform improvement across every metric.

**This was not cherry-picked:** 3 seeds were pre-committed (2026-09-20 decision) before
this run, and the full set is reported above, not a selected best-of-3.

### 2. Ablation seed count (closing the 2026-10-06 conditional decision)

- **Context:** 2026-10-06's Decision 2 left the Stage 9 ablation seed count (5 arms: E1,
  E2, E3, E4, `has_company_logo`) conditional on a real per-epoch timing, to be measured on
  "Day 3." That timing is now in hand: ~324.5s/epoch average across the two clean 5-epoch
  runs (seed 1: 325.6s avg; seed 2: 323.4s avg).
- **The arithmetic:** at 5 epochs/arm (the same count just locked in for the main
  comparison, for a fair like-for-like ablation), one full pass of all 5 ablation arms
  costs 5 arms × 5 epochs × 324.5s ≈ 135 minutes (~2.25 hours) per seed. At 3 seeds, that's
  ~6.75 hours of GPU time; at 1 seed, ~2.25 hours.
- **Decision:** 1 seed per ablation arm, not 3. Stage 9 (per `PROJECT_PLAN.md` §0.5, Day 4)
  already has to fit the full one-time test-set evaluation, the Tier 2 temporal-transfer
  test, the source-probe leakage test, Stage 7's SHAP explanations (already flagged in the
  plan as its own time risk), and Stage 8's API wiring and demo — all on one day already
  named as "the most likely day to run over." ~6.75 hours for ablation alone does not
  fit alongside that; ~2.25 hours does.
- **What I gave up:** a per-category variance estimate for the ablation — each arm's Δ
  will be a single point, not a mean ± SD like the main comparison gets. That is a real,
  disclosed reduction in rigor for the ablation specifically, not a silent one; it should
  be stated as a limitation wherever the ablation results are reported, not left implicit.
  The main 3-seed comparison above is unaffected by this — it's already complete.
- **Self-check:** *Why is it still defensible for the main comparison to report mean ± SD
  over 3 seeds while the ablation arms report only 1 seed each, when both are measuring
  model performance? What would you say if an examiner called this inconsistent?*

- **Addendum, 2026-10-08 — the cost predicted here showed up concretely:** the real
  ablation run (5 arms, seed 0) came back with every single arm's PR-AUC higher than the
  full model's, including a near-zero +0.0056 for E4 — a uniform direction across 4
  independent category removals that is at least as consistent with "the full model's
  seed-0 PR-AUC happened to land on the low side" as with "every category genuinely hurts
  PR-AUC." This is exactly the situation "what I gave up" above named in advance: with no
  second seed for any arm, there is no way to check how much of that pattern is the real
  effect of removing a category versus ordinary run-to-run training noise (already
  documented as real and non-trivial on this GPU setup — see the Stage 5 epoch-count
  entry). Full reading in `methodology.md`, "Ablation (O5)." Reported as what this run
  showed, not smoothed into a stronger claim than the data supports.

---

## 2026-10-08 — Stage 5 epoch count resolved: 5 epochs, from a measured peak, not a guess; checkpoint filenames fixed to not overwrite across seeds

- **Context:** the 6-epoch probe (seed 0) gave a real learning curve instead of a guess:

  | epoch | val F1 | ROC-AUC | train loss |
  |---|---|---|---|
  | 0 | 0.404 | 0.908 | 0.744 |
  | 1 | 0.580 | 0.941 | 0.381 |
  | 2 | 0.540 | 0.932 | 0.220 |
  | 3 | 0.607 | 0.945 | 0.125 |
  | **4** | **0.667** | 0.942 | 0.107 |
  | 5 | 0.620 | 0.934 | 0.058 |

- **Decision:** 5 epochs (indices 0–4) for the main 3-seed comparison. F1 peaked at epoch
  4 and fell at epoch 5 while train loss kept dropping sharply (0.107 → 0.058) — model
  still fitting the training data harder, validation getting worse. That is the standard
  signature of overfitting onset, not noise (epoch 2's smaller dip, by contrast, recovered
  the next epoch — ordinary run-to-run variance, not a trend reversal).
- **Why this resolves the earlier "4 vs. probe first" decision correctly:** the probe
  (logged above, same date) was taken specifically so the epoch count wouldn't be picked
  for speed before confirming convergence — this is that confirmation. 4 epochs would have
  stopped short of the real peak; 6+ would have kept training past it for no benefit.
- **A reproducibility note, logged honestly:** the first --epochs 4 run's own epoch-3
  result (F1 0.589, same seed 0) does not exactly match the 6-epoch probe's epoch-3 result
  (F1 0.607), despite nominally identical settings. This is expected GPU non-determinism
  (cuDNN/attention kernels aren't bit-exact across runs unless deterministic mode is
  explicitly forced, which this script doesn't do) — not a bug, and not a reason to distrust
  the peak-then-decline trend, which is far larger than this run-to-run noise. Worth a
  sentence in Chapter 3 if asked why two "identical" runs differ slightly.
- **Checkpoint-filename bug caught before it caused damage:** the script originally saved
  the best checkpoint to one fixed filename regardless of `--seed`, which meant running
  seed 1 next would have silently overwritten seed 0's already-good checkpoint with no
  warning. Fixed to seed-suffixed filenames
  (`distilbert_fused_state_dict_seed{N}.pt` etc.) before any further seed was run. Seed 0's
  checkpoint, already on disk from the probe (the only run whose best epoch happens to be
  epoch 4, exactly what was decided), is reused as seed 0 of the final 3-seed comparison
  rather than retrained — the checkpoint-on-best-F1 design meant it already represents the
  trained-to-peak result, so re-running it would cost ~22 minutes to reproduce (not exactly,
  per the note above) a result already in hand.
- **What I gave up:** exactness. Seed 0's "official" checkpoint was produced inside a
  6-epoch run rather than a clean standalone 5-epoch run — methodologically equivalent
  (same code path trains epoch 4 identically either way) but not identical bytes, given the
  non-determinism noted above. Chosen over spending ~22 more minutes to replace a result
  that would differ only by run-to-run GPU noise anyway.
- **Self-check:** *Why does train loss still falling while validation F1 falls count as
  stronger evidence of overfitting than validation F1 falling alone — what would it mean if
  train loss had also started rising at epoch 5?*

---

## 2026-10-08 — Stage 5 epoch count for the main comparison: delegated decision, probe to 6 epochs before locking the 3-seed run

- **Context:** the first real (full-dataset) DistilBERT+evidence run, 4 epochs, 1 seed,
  showed validation F1 still rising each epoch (0.412 → 0.566 → 0.569 → 0.589) while train
  loss kept falling fast (0.743 → 0.125). That result already beats both baselines
  (LogReg F1 0.556, RF F1 0.513), which is encouraging, but 4 epochs was an arbitrary
  starting number, not a measured stopping point — I hadn't yet seen whether F1 keeps
  climbing, plateaus, or starts falling (overfitting) past epoch 3. I asked which way to
  resolve this and was given full authority to decide ("I give you full power to take the
  right decision").
- **Options considered:** (A) lock in 4 epochs now and spend the saved time running seeds
  1 and 2 at that count (~45 min for the full 3-seed main comparison); (B) spend one more
  run (fresh, not resumed — the script doesn't support checkpoint-resume — so a full
  6-epoch run, ~33 min) on seed 0 alone first, to see epochs 4 and 5 before deciding the
  final count for all 3 seeds.
- **Why B:** O3 ("does the fused evidence improve on text-only detection") is one of this
  project's core research questions. The baseline models (LogReg, RF) were each fit to
  their own natural stopping point by their solvers in a single call — they were not cut
  short. If DistilBERT's epoch count is picked for speed before confirming it has actually
  converged, the O3 comparison silently becomes "undertrained-DistilBERT vs. fully-fit
  baseline," a different and weaker question than the one O3 asks, and that bias would be
  invisible in the final numbers unless I can point to the epoch curve and say where it
  leveled off. The checkpoint-on-best-F1 mechanism already built into the script means
  there is no downside to running longer: if epoch 5 or 6 is worse, the saved checkpoint
  stays at whichever epoch was actually best, so the extra 33 minutes either confirms 4
  was already close to optimal, or catches a real gain I would otherwise have left on the
  table for all 3 seeds.
- **What I gave up:** about 30 extra minutes today, and the possibility that this was
  unnecessary caution if epoch 4 turns out to already be the peak. Given this decision
  feeds a core RQ and the cost is small relative to the time already available this week,
  that trade was worth taking.
- **Self-check:** *Why does training the baseline models "to convergence" (via their
  solver's own stopping rule) and training DistilBERT for a fixed, arbitrarily-chosen
  epoch count threaten the O3 comparison's fairness, and what does the checkpoint-on-
  best-F1 mechanism do to make "just run a few more epochs to check" a low-risk way to
  resolve that?*

---

## 2026-10-08 — Stage 5 improved-model fusion: E1 kept as an explicit structured feature, not left implicit in DistilBERT's text input; pos_weight used as loss-level class-imbalance control

- **Context:** writing `src/models/train_distilbert.py` (the O3 "DistilBERT + structured
  evidence" model) required deciding exactly what goes into the fused feature vector
  alongside DistilBERT's text embedding, and how to carry the "identical class weighting"
  rule (2026-08-07) across to an architecture where sklearn's `class_weight="balanced"`
  doesn't apply.

### 1. E1 (suspicious-phrase lexicon) is included as a structured feature, even though DistilBERT reads the same text directly

- **Options considered:** (A) leave E1 out of the structured vector — DistilBERT already
  sees the raw words the lexicon matches against, so including E1 too looks like feeding
  the model the same information twice; (B) include E1 as a structured feature exactly
  like E2/E3/E4.
- **Why B:** two reasons. First, decisions.md (2026-10-06, Decision 2) already names E1 as
  one of the five leave-one-category-out ablation arms (E1, E2, E3, E4, `has_company_logo`)
  — that only makes sense if E1 is a distinct, removable *input* to the fused model, not
  something sitting implicitly inside the token sequence where it can't be ablated without
  also removing the text itself. Second, a hand-coded lexicon match is a much lower-
  variance signal than whatever DistilBERT might or might not learn to extract from the
  same tokens in a short fine-tuning run — handing the model the explicit flag is a
  deliberate inductive bias, not strictly redundant information.
- **What I gave up:** a cleaner information-theoretic story ("every structured feature adds
  genuinely new information DistilBERT couldn't get from the text alone"). E1 doesn't
  satisfy that; E2/E3/E4 do (they come from metadata fields DistilBERT's text input never
  sees). This is now a stated asymmetry inside "structured evidence," not something to
  discover for the first time at the viva.
- **Self-check:** *If ablating E1 removes the lexicon flag but DistilBERT still sees the
  same words either way, what exactly does the E1 ablation arm measure — and how is that
  different from what the E2/E3/E4 ablation arms measure?*

### 2. Class imbalance in the DistilBERT arm: `pos_weight` in `BCEWithLogitsLoss`, not a literal translation of `class_weight="balanced"`

- **Options considered:** (A) try to replicate sklearn's exact "balanced" formula inside
  the PyTorch loss; (B) use `pos_weight = n_negative / n_positive` on the training fold,
  the standard PyTorch idiom for binary class imbalance, documented as equivalent in
  principle rather than identical in formula.
- **Why B:** sklearn's `class_weight="balanced"` reweights both classes by
  `n_samples / (n_classes * n_samples_class)`; `pos_weight` only reweights the positive
  term inside `BCEWithLogitsLoss`. There is no architecture-neutral way to make these
  numerically identical — they operate on different loss functions entirely. Option A would
  have produced a false sense of exactness without actually matching anything.
- **What I gave up:** the ability to claim the baseline and improved models use literally
  the same class-weighting formula. They use the same *principle* (upweight the minority
  class by its training-fold imbalance ratio), applied at the point each architecture
  allows it to be applied. The controlled-comparison claim in Chapter 3/4 should say exactly
  that, not overstate it as "identical."
- **Self-check:** *Why can't `class_weight="balanced"` and `pos_weight` be made numerically
  identical, and does that difference threaten the "both arms differ in only one thing"
  guardrail, or not?*

---

## 2026-10-08 — Stage 4 lexicon design: delegated decision on tuning-contamination risk and two out-of-scope patterns

- **Context:** building the real C1, C3–C6 lexicons raised a risk I flagged before writing
  any code: the only human-labelled signal I have about these rules is the 200-posting
  Stage 2 disagreement sample. Tuning the new lexicons row-by-row against it until they
  agreed with my own prior manual judgements would be circular — the same failure mode as
  "a threshold set after seeing results is not a threshold," just applied to rule *design*
  instead of a numeric threshold. Separately, the Stage 2 audit surfaced two inconsistency
  patterns that don't fit anywhere in C1–C6: a title-vs-body role mismatch, and a
  company_profile-vs-description employer mismatch. I asked for a decision on both and was
  given full authority to resolve them myself ("do the best and most suitable way... take
  the best decision carefully").
- **Decision (lexicon design):** every C1, C3–C6 lexicon is designed on general linguistic
  principle — what a phrase actually asserts, checked against real matched text — not by
  checking agreement with the 200-posting sample. The disagreement notes
  (`reports/stage2_disagreements_for_review.txt`) were read once for qualitative inspiration
  about *categories* of failure (e.g. "topic mention vs. genuine claim"), never re-opened as
  a row-by-row tuning target while writing or adjusting a pattern.
- **Decision (two out-of-scope patterns):** neither becomes a new rule this stage. C1–C6 is
  the taxonomy already defined and partially validated; adding a rule now, after seeing
  these two specific cases, would be a post-hoc scope change driven by what the data showed
  rather than a decision made in advance. Both are logged as a named limitation /
  future-work item instead (see `methodology.md`, Stage 4 section) — real, worth stating,
  not quietly dropped.
- **What I gave up:** a stronger-sounding claim that the real lexicons "agree with human
  judgement" on the audit sample, which would have been bought by tuning to that sample and
  would not have been a fair claim to make. Also gave up two more C-rules that might have
  caught genuine inconsistencies, in favour of not changing the taxonomy's scope reactively.
- **Self-check:** *Why would tuning a new lexicon's design against the 200-posting
  disagreement sample be the same category of error as setting a threshold after seeing
  results, even though no numeric threshold is involved?*

## 2026-10-08 — Four precision bugs found and fixed during Stage 4 full-corpus validation, before any coverage figure was reported

- **Context:** after building the real C1–C6 lexicons on principle (previous entry), I ran
  `extract_all()` against the full 17,880-row corpus and manually inspected a sample of each
  rule's actual contradiction cases against the real posting text before trusting any
  number — the same discipline already used for the C2/C4 fixes documented inline in
  `extract_features.py` from first authoring. Four more precision bugs turned up this way,
  each caught by reading real matched text, not by checking against Stage 2 labels:
  (1) C1's "work from home" matched flexible-working *perks* as often as genuine
  remote-position claims (197/223 first-pass contradictions); (2) C1 ignored negation
  ("this is **not** a remote position" still matched "remote position"); (3) C6 never
  resolved "k" (thousands) shorthand, and a salary-context proximity gate
  (`_SALARY_WORD_RE`) was written but never actually wired into the matching logic, so
  unrelated dollar figures (travel reimbursement, ad-copy product costs) were compared
  against `salary_range`; (4) C3's bare "short-term"/"fixed-term" fired on unrelated text —
  95/252 "Temporary" contradictions traced to "short-term disability," a standard US
  benefits-plan phrase with nothing to do with employment type.
- **Decision:** fix all four before reporting any Stage 4 coverage figure, documenting each
  fix inline in the module (with the before/after counts) and in `methodology.md`, rather
  than reporting the first-pass numbers with a caveat. A reported figure that is known to be
  wrong is worse than a delay to fix it.
- **What I gave up:** nothing scientifically — these are corrections, not trade-offs. The
  cost was time (four debugging cycles instead of one pass), which was worth it because the
  pre-fix C1 contradiction count (223) would have been cited in the dissertation as if it
  were a real finding about telecommuting-field inconsistency, when 88% of it was actually
  about flexible-working perks.
- **Self-check:** *For each of the four bugs, what specific real posting text exposed it,
  and why did the fix not require looking at the Stage 2 audit sample to design?*

## 2026-10-08 — Decision 0.3 reconciliation: C6's numeric-escalation path uses a fixed loose margin, not a training-fold-derived threshold

- **Context:** Decision 0.3 (2026-10-06, itself flagged as reconstructed, not recovered
  original reasoning) says C6 should be a presence/structure check wherever possible, and
  that *if* a numeric-deviation comparison turns out to be needed, its threshold should come
  from non-label-conditioned training-fold statistics, not be picked by eye. Building the
  real C6 lexicon, I kept the presence/structure check (`C6_text_salary_field_absent`,
  satisfying Decision 0.3's core concern directly) but also kept a numeric-escalation path
  for when `salary_range` **is** present and a $ figure in the text falls far outside it —
  because dropping that path entirely would have meant C6's existing, already-published O1
  coverage figure (26.5% on the Stage 2 sample, cited in `methodology.md`'s "Taxonomy
  validation" table) silently stopped meaning what it says it means.
- **Decision:** the numeric-escalation margin (a figure counts as contradicting the field
  only if it falls below 0.5× the low bound or above 3× the high bound) is a fixed,
  deliberately generous constant, not a statistic computed from the training fold. This is a
  narrower implementation than Decision 0.3's literal "training-fold statistics" language,
  made because: (a) a fold-dependent threshold would make C6's definition change depending
  on which fold a posting happens to land in, which is a worse property for a rule whose
  whole point is a stable, explainable check; (b) the margin is wide enough (3–6× the
  field's own width, roughly) to function as a sanity check for "wildly different figure,"
  not a precision discriminator — which is exactly the role a label-free default should
  play; (c) it was set once, by inspecting the shape of plausible salary figures, before
  running on the full corpus or seeing any contradiction counts, not adjusted afterward.
- **Additional empirical support found for Decision 0.3's underlying concern (not part of
  the decision itself):** 10.3% of postings with a parseable `salary_range` have a low bound
  under 1,000 — almost certainly a mix of literal dollar figures, unmarked "thousands"
  shorthand, and hourly rates, with no unit indicator in the field to tell them apart. This
  is a real data-quality limitation of `salary_range` itself (logged in `methodology.md`,
  not "fixed" by guessing units), and it independently supports why Decision 0.3 preferred
  minimizing reliance on numeric comparison in the first place.
- **What I gave up:** a C6 implementation that follows Decision 0.3's threshold-sourcing
  instruction to the letter. What's gained is a simpler, label-free, fold-independent rule
  that still satisfies the decision's actual concern (no label-conditioned statistics
  anywhere in C6).
- **Self-check:** *Why does a fixed, generous, non-label-conditioned margin satisfy Decision
  0.3's real concern even though it isn't literally "training-fold statistics," and what
  would make this reconciliation wrong?*

---

## 2026-10-08 — Second incident: the field-presence fix reverted between two git commits; worksheet re-corrected, root cause of the reversion still unconfirmed

- **What happened:** after all 200 postings were coded (commit `57da423`) and I sat down to
  compute the O1 observability/agreement rates for the methodology write-up, `C3`, `C4` and
  `C5` field coverage came back at (or near) 100% again — the exact symptom of the bug
  already found and fixed on 2026-10-07. This was surprising, because `grep` confirmed the
  fix (the `_field_str` helper in `sample_for_manual_audit.py`) was still correctly on disk.
  The bug wasn't back in the code; something had changed the **data**.
- **Investigation:** `git show`/`git diff` across the worksheet's commit history
  (`498200d` → `2ec4e00` → `bd19a7d` → `57da423`) isolated it precisely. `2ec4e00` ("Fix
  Stage 2 field-presence bug; add manual coding tool") has the correct, fixed values — the
  2026-10-07 fix genuinely worked. `bd19a7d` ("Add Stage 2 reading copies (postings +
  question explanations)") was supposed to only add two new `.txt` reading-aid files, but
  `git show --stat` shows it also touched `reports/stage2_manual_audit_worksheet.csv`
  (+101/−101 lines) — and the diff shows `field_present` for C3 (41 rows), C4 (86 rows) and
  C5 (92 rows) reverting back to the pre-fix buggy values, and S001's
  `C3/C4/C5_manual_contradiction_MANUAL` reverting from `NA,NA,NA` back to the original
  `Y,Y,Y`. The commit that was meant to add two unrelated files silently carried the
  worksheet back to an earlier, already-fixed-and-superseded state.
- **Root cause of the reversion itself: not confirmed.** My working hypothesis is a sync
  conflict — the repo sits under `Documents`, a path commonly synced by OneDrive on
  Windows, and if a cached/conflicted copy of the worksheet was restored around the time of
  that commit, it would produce exactly this effect. This is a hypothesis, not a finding: I
  have not verified whether OneDrive sync was active, whether the worksheet was open in
  Excel or another program at the time, or any other explanation. **Open question for the
  student to help resolve** — if it happens a third time without being caught, it would
  silently corrupt real judgement data, which is a materially worse outcome than this time.
- **Quantifying real impact before fixing anything:** rather than assume the worst, I first
  checked how many of the 200 real manual answers were actually affected by the reverted
  `field_present` columns (as opposed to how many rows were merely re-exposed to the
  question). Result: of the 41/86/92 structurally-reverted rows for C3/C4/C5, only **10
  postings' answers were actually wrong** — S001 (C3, C4, C5, all three), S028 (C3), S045
  (C3), S126 (C3), S134 (C3), S140 (C3), S166 (C3), S176 (C4). Every other reverted row
  already had `NA` as its manual answer, meaning **the student's own careful reading had
  already caught the tool asking an impossible question and answered `NA` anyway**,
  independently of whether the underlying `field_present` flag was correct. This is good
  evidence that the 200-row audit was conducted carefully rather than by trusting the
  tool's prompts at face value.
- **Fix:** identical non-destructive method to the first incident — recomputed
  `field_present` for C2–C6 directly from the raw CSV using the already-fixed `_field_str`
  logic; where it flipped Y→N, reset the matching `_manual_contradiction_MANUAL` cell to
  `NA` **only if** it held a real, previously-given Y/N answer (the 10 postings above);
  every other cell (all E1–E4 answers, all other C-rule answers, every `notes_MANUAL`
  entry) was left completely untouched. Saved atomically (write to `.tmp`, then
  `os.replace`).
- **Verified:** re-ran the full 200-row cross-check afterward — 0/200 mismatches remain for
  C3, C4, C5 (and C2/C6, unaffected both times, confirmed still correct). Separately
  verified completeness: 200/200 postings, every required E1–E4 and C1–C6 cell holds a
  valid value, zero blanks.
- **Why this belongs in the dissertation, same reasoning as the first incident:**
  `STAGE2_CODING_INSTRUCTIONS.md` asks the O1 write-up to name at least one thing the audit
  made me revise or drop. The field-presence bug being caught a *second* time, this time as
  a file-level reversion rather than a code-level bug, strengthens that point rather than
  repeating it: the human-in-the-loop step and the surrounding verification discipline
  caught two different failure modes of the same underlying defect, at two different
  stages of the process.
- **What I gave up:** nothing recoverable — as with the first incident, no genuine
  judgement was lost; the 10 affected cells held answers to a question that should never
  have been asked, not valid judgements being overwritten.
- **Still open:** confirm with the student whether the `credibility-scoring-framework`
  folder is OneDrive-synced, and whether the worksheet was open in Excel or VS Code around
  the time of commit `bd19a7d`. Until the actual cause is confirmed, treat any future
  session that touches `reports/stage2_manual_audit_worksheet.csv` as needing a fresh
  cross-check against the raw CSV before trusting its `field_present` columns.
- **Self-check:** *why did only 10 of the ~219 structurally-reverted rows actually have a
  wrong manual answer, and what does that gap tell you about how dependent your own
  judgement was on the tool's prompts being correct versus your own reading of each
  posting?* *Separately: why does "the worksheet file reverted between two commits" need a
  different kind of fix — a file-integrity investigation and an open root-cause question —
  rather than just reapplying the same code fix and moving on?*

---

## 2026-10-07, 23:55 — Bug found and fixed: Stage 2 worksheet pre-fill wrongly marked blank employment_type/required_experience/required_education as "present" for 41/86/92 of 200 postings

- **What happened:** while coding S001 (the first posting), I noticed the coding tool's
  `--full-text` printout showed `employment_type=(blank)`, `required_experience=(blank)`,
  `required_education=(blank)` for that posting, yet the worksheet had still asked me to
  judge C3/C4/C5 contradictions on it — which should be impossible if those fields are
  genuinely blank (per `STAGE2_CODING_INSTRUCTIONS.md`, a contradiction judgement is only
  asked when `{rule}_field_present == 'Y'`). I asked whether my answers were wrong; checking
  this directly was more useful than guessing, so the underlying pre-fill script was read
  and the raw CSV cross-checked row by row.
- **Root cause:** `src/taxonomy_audit/sample_for_manual_audit.py`'s field-presence checks for
  C3, C4 and C5 used the pattern `str(r.get("field", "") or "").strip()`. `df` is loaded with
  `dtype=str, keep_default_na=False, na_values=[""]`, which still converts a blank cell to a
  float `NaN` (the column exists, so `.get()` returns that `NaN` itself, not the `""`
  default). `NaN or ""` evaluates to `NaN` because `bool(float('nan'))` is `True` in Python,
  and `str(NaN)` is the non-empty string `"nan"` — which passes a `!= ""` presence check.
  Net effect: any row where `employment_type`, `required_experience` or `required_education`
  is genuinely blank was pre-filled as `field_present = "Y"`, wrongly soliciting a manual
  contradiction judgement on a field that doesn't exist.
- **How widespread:** cross-checked all 200 rows of `reports/stage2_manual_audit_worksheet.csv`
  against `data/raw/DataSet.csv` directly (comparing `field_present` to whether the raw field
  is actually `NaN`/blank at that row's `original_csv_index`). **C3 (employment_type) wrong
  on 41/200 rows; C4 (required_experience) wrong on 86/200; C5 (required_education) wrong on
  92/200.** C2 (location) and C6 (salary_range) use the same buggy access pattern but turned
  out unaffected in practice — C2's `has_city` check requires splitting on commas into ≥3
  parts, and C6's regex requires a `\d+-\d+` shape, so the literal string `"nan"` fails both
  checks anyway and happens to land on the correct `"N"` by coincidence, not by correct
  handling. Confirmed this with the same full-dataset cross-check: 0/200 mismatches for both.
- **Fix:** added a `_field_str(row, key)` helper to `sample_for_manual_audit.py` that checks
  `pd.isna(v)` before falling back to `""`, and routed every field-presence check (C2, C3,
  C4, C5, C6) through it instead of the `or ""` pattern — including C2 and C6, which weren't
  actually wrong, so the same latent bug can't resurface there later by accident.
- **How the live worksheet was corrected (not regenerated from scratch):** re-sampling from
  scratch was rejected — it would reshuffle which 200 postings are even in the sample (the
  `RANDOM_SEED = 42` sampling is deterministic given the same input, but rebuilding the whole
  worksheet risked clobbering every `_MANUAL` answer already entered, for the sake of fixing
  three columns). Instead, a one-off correction script recomputed only the five
  `{rule}_field_present` columns against the raw CSV using the fixed logic, row by row, in
  place. Where a `field_present` flag flipped from the old (wrong) `"Y"` to the corrected
  `"N"`, the matching `{rule}_manual_contradiction_MANUAL` cell was reset to `"NA"` (the only
  valid value once the field doesn't exist) — but only if it had actually been answered;
  rows not yet reached were left untouched. Every `E1-E4_observable_MANUAL`,
  `C1_manual_contradiction_MANUAL`, and `notes_MANUAL` entry already filled in was verified
  byte-for-byte unchanged afterward.
- **Concrete effect on real data:** only S001 had been coded at the time this was found. Its
  `C3/C4/C5_field_present` flipped `Y → N` and its `C3/C4/C5_manual_contradiction_MANUAL`
  (which I had answered `Y/Y/Y`, because the tool asked) were reset to `NA`. This is a
  mechanical correction, not a re-judgement of my answer — those three fields genuinely do
  not exist on that posting, so `NA` is the only correct value, and I was never actually
  capable of answering that question correctly as it was originally asked. My E1-E4 and C1
  answers for S001 stand exactly as I gave them.
- **Verified:** re-ran the full 200-row cross-check after the fix; 0/200 mismatches remain
  for all five rules (C2, C3, C4, C5, C6).
- **Why this belongs in the dissertation, not just this file:** `STAGE2_CODING_INSTRUCTIONS.md`
  already asks the audit write-up to name at least one thing the audit itself made me revise
  or drop — this is that thing, and it's a stronger one than a borderline judgement call: the
  manual audit caught a real, previously undetected defect in the project's own tooling,
  on the very first posting coded. That's worth stating plainly in the O1 write-up in
  `methodology.md` once the full 200 rows are done, as evidence the human-in-the-loop step is
  doing real work, not rubber-stamping.
- **What I gave up:** nothing recoverable — no manual judgement was thrown away that was ever
  valid. The only cost was the few minutes spent answering three questions that should never
  have been asked.
- **Self-check:** *why does the exact same buggy access pattern produce a wrong answer for
  C3/C4/C5 but, by coincidence, a right one for C2/C6 — and why was "fix all five anyway"
  the correct response rather than "only fix the three that were actually wrong"?*

---

## 2026-10-07, 18:10 — Git commit-attribution fix: history rewritten locally via cherry-pick, not interactive rebase; push deferred to the student

- **What decided:** three commits (`b5a45aa`, `5545d37`, `6e391b4` — Stage 3, Tier 2
  legit-side sourcing, and the overnight close-out note) carried an unwanted
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` + `Claude-Session:` trailer. I
  do not want Claude attributed as a co-author in GitHub's contributor graph — my explicit
  instruction from last night. Fixed by rewriting those three commits.
- **Options considered:**
  1. **Interactive rebase (`git rebase -i`, mark as `reword`)** — the standard tool for this,
     but it opens an interactive editor per commit, which a non-interactive shell (this
     session's `device_bash`) cannot drive without extra scripting (`GIT_SEQUENCE_EDITOR` /
     `GIT_EDITOR` tricks).
  2. **`git filter-branch` / `git filter-repo`** — more powerful than needed for exactly
     three known, contiguous, top-of-branch commits; `filter-repo` wasn't confirmed
     installed, and `filter-branch` is explicitly discouraged by git itself for anything
     this small.
  3. **Branch from the shared parent + cherry-pick each commit, amending the message each
     time (`git commit -F <cleaned-message-file>`)** — chosen. Since all three commits were
     already the three most recent on `main` (no commits after them), this is equivalent to
     a reword-only rebase but fully scriptable without an interactive editor, and lets me
     verify each result before moving to the next.
- **Why this one:** option 3 does exactly what's needed with no editor dependency, and its
  intermediate state is easy to verify at each step — after each cherry-pick I diffed the
  new commit's tree against the old commit's tree (`git diff <old> <new>`) and required it
  to be empty before amending the message, so content could not silently drift. Author name,
  author email, and both author and committer dates were explicitly carried over
  (`GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars set from the original commit's own metadata)
  so the rewritten commits look, date-wise, exactly like the originals — only the message
  changed.
- **Safety steps taken before rewriting:** created `backup-pre-attribution-fix`, a branch
  pointing at the old history (tip `6e391b4`), before touching anything, so the original
  commits remain reachable and recoverable if anything goes wrong. After rewriting, scanned
  the full rewritten range (`af25cb5..a39f441`) for the strings `Co-Authored-By` and
  `Claude-Session` — zero matches.
- **What I gave up:** nothing load-bearing. The rewritten commits have different hashes from
  the ones currently on `origin/main`, which is unavoidable for any history rewrite — this
  is why the next step is a `--force-with-lease` push, not a plain push.
- **Why the push itself was not done from this session:** the task's linked development
  machine exposes a sandboxed, isolated Linux shell (`device_bash`) that is a separate VM
  from the actual Windows machine — it mounts only the connected repo folder, not the
  Windows credential manager / Git Credential Manager that normally supplies GitHub
  authentication. `git push` from that shell failed immediately with
  `fatal: could not read Username for 'https://github.com'` — there is no token or stored
  credential available to it, and entering one on its behalf isn't something I generate or
  substitute for the student. The fix must be completed by running
  `git push --force-with-lease origin main` from the student's own terminal, where GitHub
  auth already works.
- **Side-finding, logged not fixed-around:** the first `git stash` attempt during this
  work left a stray `.git/index.lock` and some `tmp_obj_*` files that blocked further git
  commands (`device_bash`'s connected folder has delete disabled by default). After delete
  permission was granted for this one folder, clearing the stale lock triggered a full
  working-tree line-ending (CRLF-vs-LF) rewrite of 9 unrelated already-committed files
  (`.gitignore`, `README.md`, two audit-history files, `data/README.md`, four `reports/*`
  files) — confirmed via `git diff -w` to be whitespace-only, zero semantic change, and
  discarded with `git checkout --` before proceeding, so none of that noise entered any
  commit.
- **Self-check:** *why is a plain `git push` not enough here, and why `--force-with-lease`
  specifically rather than plain `--force`?* — Because the commit hashes changed (the
  content is identical but the messages differ, so git treats them as different commits),
  a plain push is rejected as a non-fast-forward update; `--force` would push regardless of
  what's currently on the remote, while `--force-with-lease` refuses if someone/something
  else has pushed to `origin/main` since I last fetched it — a guard against silently
  clobbering work I don't know about.

  > ✅ **Resolved, 2026-10-07, 23:31:** pushed `git push --force-with-lease origin main`
  > from my own terminal (VS Code's integrated PowerShell, venv active). GitHub accepted it
  > cleanly: `6e391b4...09bece3 main -> main (forced update)`. `origin/main`'s tip is now
  > the trailer-free history. `backup-pre-attribution-fix` stays as a local-only branch
  > holding the old history, never pushed, costs nothing to keep.

---

## 2026-10-07, 17:30 — Tier 2 fraud-side sourcing resolved: 24 verified postings, BBB Scam Tracker, via Claude in Chrome

- **What happened:** with the development machine linked and the Claude in Chrome
  extension installed (walked through step by step this morning), BBB Scam Tracker's
  "employment" search became reachable — Claude in Chrome, driving my real signed-in
  Chrome, loads the page normally where both the sandboxed browser pane and plain WebFetch
  were stopped by a Cloudflare "Just a moment..." challenge. No bypass technique was used
  anywhere — every block was handled by waiting and retrying, or by paginating once the
  page had already loaded cleanly.
- **What was collected:** read through BBB Scam Tracker's "employment" search results,
  pages 1–8 (`from=0` through `from=70`, ~80 individual reports read in full), and kept
  every report that contains **genuinely reproduced posting-adjacent text** — a quoted
  email, SMS, or chat message from the scammer naming a role, pay rate, duties, or an
  application step — rejecting reports that are narrative-only ("they called and asked if I
  could hear them") or too corrupted to use (one report's message text was obfuscated with
  stray `?` characters past the point of being legible). **24 reports passed this filter**,
  comfortably inside the 20–30 target set in the 2026-09-20 scope-cut decision.
- **Provenance:** each BBB report has its own permanent URL
  (`https://www.bbb.org/scamtracker/lookupscam/<Scam ID>`), confirmed by inspecting the
  page's own DOM (`aria-labelledby="result-<id>-title"` on each result's link) rather than
  guessing — this resolves the provenance question left open overnight. Every one of the 24
  records in `data/raw/tier2/tier2_fraud_raw.jsonl` carries its own unique `source_job_id`
  (the BBB Scam ID) and `source_url` (the permalink), exactly mirroring how
  `tier2_legit_raw.jsonl` carries `source_job_id`/`source_url` for Greenhouse/Lever.
- **Schema decision:** the EMSCAD-shaped structured fields (`title`, `location`,
  `salary_range`, etc.) are left `null` for every fraud-side record, rather than invented
  from the narrative or populated from BBB's "Victim Location" (which is where the *victim*
  lives, not a claimed job location — not the same field semantically, so it does not belong
  in `location`). BBB-specific context (the category tag, the business name the scammer
  used, the date reported, and dollars lost) is kept in separate `bbb_*` fields instead of
  forced into EMSCAD columns. This keeps the E3/E4 asymmetry exactly as already decided and
  disclosed in Decision 0.4 (2026-10-06) — I am not quietly inventing structure on the fraud
  side to make it look more symmetric than it is.
- **Data-quality finding, worth disclosing in Chapter 6:** the same scam narrative (a
  "David Smith" / "Sheriff Gossling" personal-assistant check-fraud report) appears at least
  three times in BBB's own database under three different Scam IDs (442452, 442451, and one
  more seen in an earlier page) — byte-for-byte identical text, different report IDs. This
  report was excluded from the 24 anyway because it has no quoted posting/ad text, but the
  pattern itself matters: BBB Scam Tracker contains genuine near-duplicate injection (the
  same report filed, or re-filed, multiple times), so any later aggregate statistic drawn
  from BBB counts ("X% of scam reports are...") would need deduplication first. Noted here
  rather than silently worked around.
- **What I gave up:** nothing further was attempted after reaching 24 — pagination stopped
  once comfortably past the 20-minimum / 30-target band, rather than continuing to scrape
  every one of BBB's "employment" pages. A larger fraud-side set was available (BBB reports
  10,000+ results for this search) but collecting it all would have cost Day 1 time for a
  number the target band already calls sufficient, and Tier 2 is held-out validation only —
  more volume here doesn't buy anything a training set would need.
- **Self-check:** *Why does "Victim Location" not belong in the same `location` field
  EMSCAD uses, even though both are nominally about where a job is?*

---

## 2026-10-07, 00:40 — Tier 2 fraud-side sourcing: fetchable web tools confirmed a dead end tonight; deferred to daylight with a time-boxed browser-assisted plan

- **What was tried:** three real attempts, not a guess that it wouldn't work. (1) General
  web search for scam job postings with reproducible full text — returned only news
  coverage and BBB aggregate-study articles *describing* scam patterns, never quoting a
  real posting's actual text. (2) Direct fetch of BBB's Scam Tracker — its search is
  JavaScript-driven; a static fetch only sees the empty shell, not individual reports. (3)
  Direct fetch of Reddit r/scams — blocked outright (declined for legal reasons, same as
  any site this tool declines; not worked around with another method). (4) Direct fetch of
  two specific DOJ/FTC documents likely to quote evidence — both describe schemes in their
  own summary language ("promising job seekers... $6,000 in guaranteed monthly profit")
  rather than reproducing the actual posting text verbatim.
- **Why this matters:** unlike the legitimate side (Greenhouse/Lever expose a public,
  structured, machine-readable API because job boards want to be found), scam reporting has
  no equivalent. The primary artefact — the actual posting text — lives inside individual
  human reports (BBB Scam Tracker entries, Reddit threads, screenshots), not in any
  bulk-fetchable or API-exposed form. This is a genuine structural difference between the
  two sourcing problems, not a tooling shortfall on one side.
- **Decision:** do not invoke the pre-planned qualitative-only fallback yet — that is a real
  decision with Chapter 6 limitations consequences and deserves one focused, real attempt
  first, not a call made because fetch-only tools hit a wall at 1am. Instead: defer to
  daylight hours of Day 1, with two concrete options kept open — (a) link the development
  machine to the AI session via the desktop app, giving genuine interactive browser access
  (can search, click, scroll through BBB/Reddit), run for a hard-capped ~90 minutes; or (b)
  manual browsing and curation, done with a fresh, attentive read rather than at 1am. If
  neither reaches ~20 verified fraudulent postings by end of Day 1, the fallback decided
  2026-10-06 triggers exactly as already planned — that outcome was anticipated, not a
  surprise.
- **What I gave up:** a few hours tonight that could have gone toward fraud-side sourcing,
  in exchange for not producing low-quality, badly-documented provenance records from a
  tired, rushed attempt. Given this data becomes part of a held-out validation set whose
  entire value rests on trustworthy labels, a smaller number of carefully-verified postings
  is worth more than a larger number collected carelessly.

  > ✅ **Resolved, 2026-10-07, 17:30:** option (a) worked — see the entry above. 24 verified
  > postings collected, well inside the 20–30 target. Tier 2 fraud-side sourcing is closed.

- **Self-check:** *Why does the legitimate side of Tier 2 have a clean public API while the
  fraud side doesn't — what's structurally different about who wants a scam report to be
  easy to find by machine?*

---

## 2026-10-07, 00:40 — Tier 2 legitimate-side target exceeded (130 vs. 30–50 planned); kept in full

- **What happened:** the Greenhouse/Lever sourcing script (60 candidate company slugs,
  self-validating — tries each, keeps only what responds) returned 130 postings from 26
  real companies (24 Greenhouse, 2 Lever), capped at 5 postings/company for diversity. This
  is well above the 30–50 figure in the sprint plan and in `decisions.md`'s 2026-09-20
  Tier 2 scope-cut entry.
- **Options considered:** (A) subsample down to ~50 to match the original target exactly;
  (B) keep all 130.
- **Why B:** Tier 2 is held-out validation only — never trained on, never used to fit
  anything — so extra legitimate-side volume doesn't risk anything a training set would
  (no risk of the model fitting to Tier 2 noise, no risk to the leakage-controlled
  train/val/test boundary, which is Tier 1 only). More postings only makes the temporal-
  transfer evaluation's legitimate-side estimate more stable, and diversity across 26
  companies (vs. fewer companies at higher volume) better represents real-world variety in
  job-board formatting and writing style. There is no stated reason in any existing decision
  to prefer exactly 30–50 over "however many clean, diverse postings are available" — the
  30–50 figure was a planning estimate for what seemed achievable, not a methodological
  requirement.
- **What I gave up:** nothing substantive. The one thing to watch: this leaves Tier 2
  asymmetric in volume (130 legitimate vs. a fraud-side target of only 20–30, assuming that
  target is even met) — this asymmetry must be reported plainly in `methodology.md`
  alongside the fraud-side numbers once both are known, not presented as if the two sides
  were collected at comparable scale.

  > ✅ **Numbers now final, 2026-10-07:** 130 legitimate vs. 24 fraudulent. The asymmetry is
  > real (5.4:1) and must be stated plainly wherever Tier 2 composition is reported.

- **Self-check:** *Why is extra Tier 2 legitimate-side volume safe to keep, when extra
  Tier 1 training data in the wrong place would not be?*

---

## 2026-10-06, 23:59 — Correction: Decision 0.2's title-hash grouping over-merges; reverted to description-hash only

- **What happened:** Stage 3's partitioning code was built tonight implementing Decision
  0.2 exactly as logged — MD5-on-normalised-description UNION MD5-on-normalised-title. It
  ran, passed all 9 tests, and produced a plausible-looking top-line number (56.68% of the
  corpus in a duplicate group). Before committing, a diagnostic was run on the 15 largest
  groups rather than trusting that number — this is exactly the kind of check the project's
  own continuity protocol calls for, and it caught a real bug.
- **What the diagnostic showed:** only the known "English Teacher Abroad" group (714
  records, 7 titles, 28 descriptions) looks like a genuine repost campaign. Every other
  large group is a false merge — e.g. "Software Engineer" (572 records, **118 distinct
  titles, 501 distinct descriptions**), "Customer Service Associate" (396 records, 48
  titles, 304 descriptions). These are hundreds of genuinely unrelated postings from
  different companies, chained together because they happen to share a common, generic job
  title. Because grouping is transitive, one coincidental title or description match can
  snowball into merging hundreds of otherwise-unrelated records.
- **Why this matters:** this is a worse version of the exact failure mode Decision 0.2
  already rejected a cheaper method for in September (the 12-token-prefix proxy, rejected
  for merging 48.9% of the corpus). Tonight's title-hash union merged 56.68% — higher than
  the method already rejected for over-merging. Shipping this would have corrupted the
  train/validation/test split (forcing genuinely distinct postings into the same partition
  for no real reason) and reported a false "duplication rate" in the methodology chapter.
- **Decision:** revert to description-hash-only grouping (Decision 0.2's Option A, already
  considered and logged in September). This reproduces the already-measured, already-
  verified figures from the original August audit (4,762 records / 26.6%, largest group
  417) rather than a new, broken number. The known cost — the "English Teacher Abroad"
  campaign fragmenting across several groups under description-only hashing — is accepted
  as a disclosed limitation, exactly as Option A always represented it in the original
  Decision 0.2 analysis.
- **What I gave up:** the specific benefit Decision 0.2 was designed to provide (catching a
  campaign's stragglers that vary body text but reuse a title). Tested in practice, it
  doesn't work at corpus scale — generic titles are far more common than distinctive ones,
  and there's no cheap way tonight to tell them apart. A real fix (e.g. requiring title
  match AND some minimum description similarity, or proper near-duplicate clustering) is
  future work, same as Decision 0.2 already said about MinHash/shingling.
- **Self-check:** *Why did a method designed around one specific, validated example
  (English Teacher Abroad) fail so badly elsewhere, and what would have happened if the
  15-largest-group diagnostic hadn't been run before committing?*

---

## 2026-10-06, 23:50 — Decisions 0.3 and 0.4 resolved (delegated authority)

- **Context:** both decisions were scheduled for Day 1 morning, but Decision 0.3's original
  framing could not be recovered from the project files — only a one-line pointer existed.
  The student explicitly delegated authority to resolve both now rather than lose Day 1
  morning time rediscovering lost context. Logged honestly: 0.3 below is a reconstruction,
  not recovered original reasoning, and is flagged as such.

### Decision 0.3 — label-conditional statistics in design (C6 viability)

- **Reconstructed problem statement (not recovered from the original record):** C6 compares
  a salary figure mentioned in posting text against the structured `salary_range` field.
  Unlike C1 (a clean binary contradiction — remote vs on-site language), "mismatch" for a
  salary comparison could require a numeric deviation threshold, and setting that threshold
  by checking which deviations correlate with the fraud label would be a quiet form of
  leakage into rule *design* — not test-set leakage in the usual sense, but the same
  underlying problem as the existing guardrail "a threshold set after seeing results is not
  a threshold."
- **Decision:** C6 is defined as a presence/structure check wherever possible — e.g. "the
  text names a specific dollar figure while `salary_range` is absent entirely" — which needs
  no numeric threshold and therefore no label-conditioned statistics at all. Only if Stage 4
  finds this insufficient to produce a usable signal does a numeric-deviation version get
  considered, and if so its threshold must be set from training-fold descriptive statistics
  that do not condition on the label.
- **What I gave up:** a richer C6 that captures "salary number present but implausibly high
  or low," not just "salary number present but field missing." Given C6 already has the
  lowest evaluable coverage of all six rules (7.6% provisional), this is a small loss.
- **Self-check:** *Why would setting a numeric mismatch threshold by looking at which
  deviations correlate with the fraud label count as leakage, even though it never touches
  the test set?*

### Decision 0.4 — Tier 2 field symmetry (can E4 fire on the fraud side?)

- **Decision:** (1) during Day 1 sourcing, prefer fraud sources that document some
  structured fields over pure text dumps, reducing the asymmetry at the source rather than
  only measuring it afterward; (2) E1/E2 remain Tier 2's primary evidence, since both depend
  on posting text rather than how much structured metadata a given source happened to
  capture; (3) Tier 2's E3/E4 ablation results are reported with the asymmetry disclosed as
  a named limitation, not dropped from the experiment — E4 is the project's actual
  contribution, and discarding it from Tier 2 to dodge the confound would be a worse choice
  than measuring and disclosing it; (4) the source-probe leakage test already decided
  2026-08-07 is run specifically flagging E3/E4 feature importance, so the size of the
  confound is measured, not guessed.

  > ✅ **Outcome, 2026-10-07:** BBB Scam Tracker reports document almost no structured
  > fields (no salary_range, no employment_type, etc. — only a free-text narrative plus a
  > handful of BBB-specific metadata that isn't EMSCAD-shaped). Clause (1) above could not
  > be satisfied in practice — BBB simply doesn't offer a more structured alternative for
  > fraud reports the way Greenhouse/Lever do for legitimate postings. Clauses (2)–(4) stand
  > as planned: Tier 2's fraud side is text-heavy, EMSCAD-shaped fields are null, and this is
  > reported as a disclosed asymmetry, not hidden.

- **What I gave up:** a clean, confound-free Tier 2 E4 result. What's gained instead is an
  honest, measured one.
- **Self-check:** *Why is dropping E3/E4 from Tier 2 entirely a worse choice than measuring
  and disclosing the asymmetry, given E4 is the project's actual contribution?*

  > **Addendum, 2026-10-08 — the scope is larger than this decision anticipated.** The
  > source-probe leakage test (design logged in the Stage 9 Part 3 entry below) came back
  > at ROC-AUC=1.0000 / balanced_accuracy=1.0000 — perfect separation between EMSCAD and
  > Tier 2 using only the 46 structured E1-E4 features. Investigated with `device_bash`
  > rather than accepted at face value, 2026-10-08: `has_company_logo`/`has_questions` are
  > 0% missing in EMSCAD's source CSV (audited at Stage 1 — `load_emscad.py`'s own
  > docstring, "0% missing — real values only, never null") and 100% missing across ALL 154
  > Tier 2 postings — the 24 BBB Scam Tracker fraud reports AND the 130 Greenhouse/Lever
  > legitimate postings alike, not only the fraud side this decision named. The other seven
  > STRUCT_COLS fields are at or near 100% missing on both Tier 2 classes too (exact counts
  > in `methodology.md`, "Tier 2 (O5)"). This is a Tier-2-collection-wide artefact — neither
  > side of Tier 2 ever captured these nine fields — not a fraud-vs-legit asymmetry within
  > Tier 2, which is a bigger scope than clause (4)'s "fraud-side sparsity" framing
  > anticipated. The same clause's response (measure and disclose, don't drop the
  > experiment) still applies and is what Stage 9 Part 3 did.
  >
  > **Consequence flagged, not yet separately measured:** EMSCAD's own fraud/legit split
  > makes total E3 missingness disproportionately a fraud cue (part of why E3 was included
  > as an evidence category at all), so a model trained on EMSCAD may read every Tier 2
  > posting's near-total missingness as "looks suspicious" regardless of its real label.
  > This is a plausible reading of part of T1/T3's pattern (`methodology.md`), reported
  > there explicitly as inference, not as an independently verified result.
  >
  > **Self-check:** *why does a perfect source-probe score mean Tier 2's absolute transfer
  > numbers must be read with a collection-artefact caveat, rather than meaning E3/E4 are
  > "broken" as features?*

---

## 2026-10-06 — Five-day sprint compression: deadline, Tier 2 time-boxing, ablation contingency, triage order

- **Context:** the actual deadline is 5 days from today (2026-10-06), not "~1 month from
  2026-08-27" as every project file has stated — that earlier date has already passed. This
  entry supersedes the old deadline wherever it appears, until the exact programme-office
  date is confirmed and logged in its place.

### 1. Tier 2 collection is time-boxed to Day 1 only

- **Options considered:** (A) keep the 1-week checkpoint decided 2026-09-20; (B) compress
  the checkpoint to a single day with the same fallback rule; (C) drop quantitative Tier 2
  entirely, right now, with no attempt.
- **Why B:** with 5 days total and Stages 3–9 plus three dissertation chapters, a paper, and
  a declaration still ahead, a week-long checkpoint no longer exists — the whole sprint is a
  week. Option C gives up the one finding no reviewed EMSCAD paper has produced (does a model
  survive contact with contemporary fraud) before even trying. Option B keeps that chance
  alive for exactly one day and refuses to let it spend a second one if it fails.
- **Explicitly accepted risk, stated directly by me:** I am not chasing down formal
  institutional ethics sign-off for Tier 2 primary data collection before collection starts
  this week, given the timeline. This stays logged as an open item (see `project.md`) and
  must appear as a stated limitation in Chapter 6 — not something I quietly skip and never
  mention.
- **What I gave up:** the chance that fraud-side sourcing just needed 2–3 days, not 1.
- **Self-check:** *Why does compressing the checkpoint from a week to a day not change the
  fallback rule itself, only when it fires?*

### 2. Ablation seed count is conditional, decided on Day 3 from a real timing, not guessed now

- **Decision:** the main baseline-vs-improved comparison keeps 3 seeds (closed 2026-09-20,
  unchanged). The leave-one-category-out ablation arms (E1, E2, E3, E4, `has_company_logo` —
  5 arms) may drop to 1 seed each if 3×5 does not fit the compute budget measured by timing
  one real DistilBERT fine-tuning run on Day 3.
- **Why conditional rather than decided now:** I don't yet have a real per-run time to reason
  from — guessing now risks either wasting Day 3 on an avoidable cut or discovering too late
  that it was necessary. One timed run on Day 3 settles it with evidence instead of a guess.
- **What I gave up:** certainty about the shape of Day 3's schedule, in exchange for not
  pre-committing to a cut I might not need.
- **Self-check:** *Why is it defensible for the main comparison and the ablation arms to end
  up using a different seed count, when both measure performance?*

### 3. Triage order, fixed in advance

- **Decision, in order:** (1) the research paper is cut first — it may finish after the
  5-day window if there's slack, named now as the most likely casualty, not discovered on
  the last day; (2) ablation seed count reduces per Decision 2 above; (3) Tier 2 depth
  reduces further or falls back to qualitative-only (already time-boxed per Decision 1);
  (4) never cut: leakage-controlled partitioning, calibration, the test-set-used-once rule,
  the 200-posting manual audit, and the honest stub-vs-real distinction in the API.
- **Why fix this now:** deciding what to cut while exhausted on Day 4 night produces worse
  decisions than deciding it now, calmly, with the whole week still ahead. I was explicit
  that I do not want the manual audit or the core pipeline's correctness touched for any
  reason — this order protects exactly that.
- **What I gave up:** flexibility to reorder this under pressure. That's deliberate.
- **Self-check:** *Why is the manual audit protected ahead of the research paper, when the
  paper is also a formal deliverable?*

---

## 2026-09-20 — Correction: hardware constraint was wrong; DistilBERT will be fine-tuned, not frozen

- **Correction, not a new decision:** every project file (`project.md`, `SKILL.md`,
  `build.md`, and this file's own "Frozen vs. fine-tuned DistilBERT" pending entry) states
  "no dedicated GPU" as a hard constraint. **This was wrong.** My laptop has an RTX 3050
  (gaming laptop, 16GB RAM). This constraint was assumed at proposal stage and never
  actually checked against my own hardware.

- **Consequence — resolves the frozen-vs-fine-tuned question:** with a CUDA-capable GPU,
  fine-tuning DistilBERT (66M parameters) is feasible in hours, not days. Fine-tuning also
  reliably outperforms frozen embeddings for domain-specific text classification. **Decision:
  fine-tune, not frozen.** This also removes the earlier worry about needing an external
  environment like Colab for a seeded run — everything now runs locally, which is better for
  reproducibility, not just faster.

- **Why logged as a correction, not silently fixed:** the same principle as the "English
  Teacher Abroad" correction earlier in this file — the wrong assumption stood for weeks and
  shaped planning (e.g. it's the entire reason "frozen vs. fine-tuned" was ever a real
  question). Recording that it was wrong, and why it wasn't caught earlier, is worth more in
  a viva than quietly updating `project.md`'s hardware line with no trace.

  > ✅ **Resolved, 2026-10-06, 22:56:** the CPU-only `torch` build was replaced with the
  > CUDA 12.4 build (`torch==2.6.0+cu124`) on the first try — a matching wheel existed for
  > Python 3.13 on Windows, so the Python-3.13-wheel-lag risk flagged earlier did not
  > materialise. `torch.cuda.is_available()` confirmed `True` against the RTX 3050. No
  > fallback (separate venv, frozen embeddings) was needed. `requirements.txt` needs
  > regenerating to reflect this.

- **Self-check:** *Why was "no GPU" assumed for months without being checked, and what
  single fact changed once it was?*

---

## 2026-09-20 — Scope-cut decisions given the confirmed ~1 month deadline

- **Context:** the actual submission deadline was confirmed for the first time on
  2026-08-27 as approximately one month away. Full rigor on all nine stages as originally
  scoped does not fit that timeline for a single developer. Five related decisions were
  made together, deliberately, in one CONVERGENT session, rather than left to erode
  piecemeal under time pressure later.

  > ⚠️ **Superseded, 2026-10-06:** the "~1 month" deadline this section refers to has
  > elapsed. The decisions below (rules-only cut, fine-tuned DistilBERT, reduced Tier 2,
  > 3 seeds, SHAP-only, architecture review skipped) all still stand — they were not
  > reopened — but the deadline context is the 5-day sprint recorded above, not this entry.

### 1. Rules-only baseline (E2+E3+E4, no text model): CUT

- **Options considered:** (A) keep it as a third model arm; (B) cut it entirely.
- **Why cut:** it was always logged as optional ("does the transformer earn its
  complexity?"). Stage 9's leave-one-category-out ablation already measures how much E4
  alone contributes, via a different but overlapping route, without a whole separate
  training arm, retraining, and extra ablation rows.
- **What I gave up:** a clean, standalone answer to "how far would rules alone get me,
  with zero text model at all." The ablation study answers a related but not identical
  question.
- **Self-check:** *What question would the rules-only baseline have answered that the
  ablation study doesn't cover, and why is losing that answer acceptable here?*

### 2. Tier 2 depth: REDUCED collection (~50–100 postings), not full, not zero

- **Options considered:** (A) full collection (300–600, as originally planned); (B) reduced
  collection (~50–100); (C) qualitative-only (the pre-planned 2026-08-07 fallback).
- **Why reduced, not the extremes:** qualitative-only (C) discards the one finding no
  reviewed paper has produced — whether an EMSCAD-trained model survives contact with 2026
  fraud — and that's too valuable to give up pre-emptively. Full collection (A) risks
  cannibalising time from Stages 3–9 if it overruns; a project with no finished pipeline is
  worse than one with a modest, honestly-scoped Tier 2. A reduced set, reported with wide
  confidence intervals and explicitly labelled as time-constrained, is a legitimate,
  disclosed limitation rather than a hidden shortcut.
- **What I gave up:** statistical power. A 50–100 posting Tier 2 will have wide confidence
  intervals; this must be stated plainly, not minimised.

  > ⚠️ **Update, 2026-10-06:** the 1-week checkpoint below is now a 1-day checkpoint — see
  > the 2026-10-06 entry above. The reduced target (20–30 fraud / 30–50 legit) is unchanged.

  > ✅ **Final numbers, 2026-10-07:** 130 legitimate (kept in full, see entry above) / 24
  > fraudulent (see entry above). Both targets met or exceeded within the Day 1 time-box.

- **Self-check:** *Why is a small, honestly-reported Tier 2 more defensible than either
  collecting the full 300–600 or abandoning quantitative Tier 2 entirely?*

### 3. Reproducibility seeds: 3, not 5 — and the "what does five seeds mean" question is now settled

- **The seed-count reduction:** ablation alone multiplies retrains (~5 category removals ×
  multiple models × seeds); this compounds fast even with GPU acceleration. 3 seeds still
  supports mean ± SD reporting and is a documented, disclosed reduction, not a silent one.
- **The definition question (previously open, now resolved):** "repeated across N seeds"
  means N *model initialisations* run against **one fixed train/validation/test split** —
  not N different splits. This is the only reading compatible with the existing guardrail
  that the test set is used once; N different splits would mean N different test sets.

  > ⚠️ **Update, 2026-10-06:** whether the ablation arms specifically keep 3 seeds or drop
  > to 1 is now conditional on a Day 3 timing measurement — see the 2026-10-06 entry above.
  > The main comparison's 3 seeds are unaffected.

- **What I gave up:** some robustness in the noise estimate on the test set (~130 fraud
  postings), compared to 5 seeds.
- **Self-check:** *Why is "5 different splits" incompatible with "test set used once," and
  what does the seed count actually vary instead?*

### 4. Explainability: SHAP only, LIME dropped

- **Options considered:** (A) both SHAP and LIME, as originally planned; (B) SHAP only.
- **Why SHAP alone:** SHAP has stronger theoretical grounding (Shapley values, consistency
  guarantees) and handles both the structured evidence vector and text attribution
  reasonably well in one framework. Building and validating two separate explanation
  pipelines — each needing its own fidelity testing — isn't worth the cost under this
  timeline when SHAP alone satisfies O4's fidelity-testing requirement.
- **What I gave up:** a second, independent explanation method to cross-check SHAP's output
  against. `Research_Objectives_and_Questions_Final.docx` names both SHAP and LIME as
  examples ("e.g."), not a hard requirement of exactly two methods, so this doesn't violate
  the objective as written — but the .docx wording should be checked before submission.
- **Self-check:** *Does dropping LIME violate Objective 4 as formally written, or does its
  "e.g." wording leave room for this?*

### 5. Divergent architecture review: skipped, time-driven

- **Context:** this was logged as a pending decision since 2026-08-07 — survey alternatives
  (gradient boosting, sentence-transformer + gradient-boosted classifier, other lightweight
  transformers) before committing to TF-IDF + DistilBERT fusion.
- **Decision:** given the confirmed deadline, this survey is not done. The original design
  is committed to as-is.
- **Why this is acceptable to state plainly rather than quietly skip:** the honest position
  in a viva is "I did not conduct a full landscape review before committing to this
  architecture, because of the timeline, and I can name what that costs me" — not silence
  on the question, and not a retrofitted justification pretending the review happened.
- **What I gave up:** the ability to say with evidence that TF-IDF + DistilBERT fusion was
  chosen over specific, considered alternatives. It was chosen at proposal stage and never
  re-examined against the landscape.
- **Self-check:** *Why is honestly stating "I skipped this survey because of time" better
  than either silently skipping it or fabricating a comparison that wasn't done?*

---

## 2026-09-20 — Near-duplicate grouping method for Stage 3 (Decision 0.2, resolved)

- **Decision:** exact-normalised MD5 hashing on `description` (already built and tested in
  the audit script), with a **secondary grouping key on normalised `title`** added at low
  implementation cost.

- **Options considered:**
  - (A) Exact-normalised MD5 hashing only (already measured: 4,762 records / 26.6% in a
    duplicate group, but fragments the 715-record "English Teacher Abroad" campaign across
    15 separate groups).
  - (B) First-12-token hash proxy (already measured: merges 48.9% of the corpus — likely
    over-merging unrelated postings sharing a generic opening line).
  - (C) MD5 on description, plus a second grouping pass on normalised title text.

- **Why C:** option A under-groups (misses some real near-duplicates); option B over-groups
  badly (merges nearly half the corpus, a worse failure mode). Many campaigns reuse a
  near-identical title even when body text varies slightly — adding a title-based grouping
  key catches some of what pure description-hashing misses, at minimal new code (reuse the
  same `normalise()` + MD5 pattern already written, applied to `title` instead of
  `description`, then union the two groupings).

- **What I gave up:** a fully rigorous near-duplicate solution (e.g. MinHash/shingling)
  that would catch paraphrased campaigns with both different titles and different bodies.
  Not pursued, given the deadline — title+description exact-hash union catches the
  documented failure case (English Teacher Abroad) without new algorithmic complexity.

- **Revisit if:** time permits after Stage 3, or if Stage 3's measured duplicate-group
  statistics look implausible given what title+description hashing should catch.

- **Self-check:** *Why does adding a title-based grouping key specifically address the
  fragmentation problem measured in the "English Teacher Abroad" campaign?*

---


## 2026-08-27 — Reject four candidate "second datasets"; reaffirm independently-collected Tier 2

- **Decision:** None of four externally-suggested datasets — a 2026 Kaggle "Fake Job Posting
  Detection" competition, DIFrauD's "Job Scams" domain, the Internship-Job-Scam-Dataset, and
  ScamShield — are adopted as Tier 2. The original independently-collected, provenance-labelled
  contemporary set (decided 2026-08-07, below) stands unchanged.

- **Options considered:**
  - (A) Adopt the Kaggle 2026 competition as a "primary modern benchmark" (per an external
    report's recommendation).
  - (B) Adopt DIFrauD's Job Scams split, since it is a real, peer-reviewed benchmark
    (Boumber, Qachfar & Verma, LREC-COLING 2024).
  - (C) Adopt the Internship-Job-Scam-Dataset for its three-level risk framing.
  - (D) Check each against its primary source before adopting any of them.

- **Why I chose this:** Two unattributed PDF reports (no named authors, no institutional
  affiliation) recommended these datasets, and one was suggested by my supervisor via a
  direct DIFrauD link. Rather than accept either at face value, I checked each dataset's own
  card/page directly. All four trace back to EMSCAD:
  - The Kaggle competition (kaggle.com/competitions/fake-job-posting) is a Computational
    Intelligence module assignment at Cardiff Metropolitan University — 12,001 rows, 18
    columns, 95.1%/4.9% class split (19.4:1, matching EMSCAD almost exactly), and its own
    reference list cites Vidros et al. (2017), EMSCAD's origin paper.
  - DIFrauD's dataset card states directly: "The Employment Scam Aegean Dataset, henceforth
    referred to as the Job Scams dataset..." — it is EMSCAD, cleaned and deduplicated to
    14,295 records, with every structured field discarded (only `text` and `label` remain).
  - The Internship-Job-Scam-Dataset's own card states it was "adopted from... the Employment
    Scam Aegean Dataset (EMSCAD)." Its "suspicious" class is partly built by relabelling
    existing legitimate EMSCAD text under a new class (`rule_augmented_suspicious_variant`),
    not new data.
  - ScamShield sources its job data from EMSCAD, mixed with unrelated SMS spam data and
    ~255 LLM-generated (Gemini) synthetic examples.

  None of these provide temporally independent 2026-era postings — using any of them as
  Tier 2 would test an EMSCAD-trained model against EMSCAD again, defeating the entire
  purpose of the temporal-transfer experiment. DIFrauD and the Internship dataset also
  strip structured metadata, which would make E2, E3 and E4 — the actual research
  contribution — impossible to evaluate on them regardless of the temporal question.

- **What I gave up:** A ready-made, no-collection-required Tier 2. None exists that meets
  both requirements (genuinely independent of EMSCAD, and metadata-rich enough for E2–E4).

- **Bonus finding:** The Internship-Job-Scam-Dataset's row preview independently confirms
  the correction below — its "English Teacher Abroad" rows carry `original_fraudulent: 0`,
  corroborating via an unrelated third party that this cluster is legitimate, not a fraud
  campaign as the original 2026-08-07 entry stated.

- **Revisit if:** A genuinely independent, metadata-preserving, 2026-era recruitment fraud
  dataset is found and its primary source confirms it is not EMSCAD-derived.

- **Self-check:** *Why does a dataset being real and peer-reviewed (DIFrauD) not automatically
  make it suitable as my Tier 2 — what two separate requirements does it fail?*

---

## 2026-08-27 — Correction to the 2026-08-07 duplicate-postings decision

- **Correction, not a new decision:** The entry below (2026-08-07, "Group duplicate postings
  before splitting the data") states the "English Teacher Abroad" cluster is an example of a
  *fraudulent* campaign repeated with small changes. **This is factually wrong.** Measured
  on the real CSV: the cluster (715 records under a text-prefix match; the largest
  exact-normalised group, 417 records) is **100% legitimate, 0% fraudulent.**

- **The decision itself still stands**, on independent grounds: the fraud class is
  separately measured at 40.3% duplicated (349 of 866 records in a duplicate group of
  size > 1), which alone justifies group-aware partitioning. Only the illustrative example
  in the original entry was wrong, not the reasoning.

- **Why this is logged as a correction rather than a silent edit:** the original entry is
  left exactly as written below, because a mistake caught and corrected is worth more in a
  viva than a record that was quietly fixed. If asked, the honest answer is "I stated the
  wrong example when I wrote this in August, found it wrong during the data audit, and
  corrected it without changing the underlying decision."

- **Self-check:** *What did I originally claim about the "English Teacher Abroad" cluster,
  what did the measurement actually show, and why didn't the error change the decision?*

---

## 2026-08-27 — Uniform "evaluable coverage" definition for C1–C6; defer C2 to Stage 4

- **Decision:** All six consistency rules now use one consistent definition of "evaluable"
  (both operands present, so the rule could actually attempt a comparison — not merely that
  text exists nearby). C1 and C3 get a same-day symmetric pattern fix (bounded vocabulary,
  same category as each other). C2 is deferred entirely to Stage 4 — its field coverage
  (88.4%) is reported as an explicit upper bound, with no evaluable figure until then.

- **Options considered:**
  - (A) Apply the loose definition (field present + text non-empty) to all six rules.
  - (B) Build a quick regex proxy for every rule, including C2.
  - (C) Apply the strict definition uniformly, with category-appropriate treatment: fix
    bounded-vocabulary rules now, defer the one open-vocabulary rule.

- **Why I chose this:** The original audit script measured "evaluable" two different ways —
  strict for C4–C6, loose for C1–C3 — which understated the true gap between field coverage
  and real coverage. Applying the loose definition everywhere (A) would have overstated
  coverage across the board. Building a proxy for C2 (B) was rejected specifically: C2's
  premise is that a place name in free text disagrees with the structured `location` field —
  an open-vocabulary problem (any place name on Earth), unlike C1/C3's bounded vocabularies
  (a fixed set of remote/on-site or employment-arrangement phrases). A quick C2 proxy would
  become a second, weaker implementation of the rule, guaranteed to disagree with the real
  Stage 4 location matcher.

  Measured result: C1 field coverage 100.0%, evaluable 10.5%. C2 field coverage 88.4%,
  evaluable deferred. C3 80.6% / 12.2%. C4 60.6% / 30.2%. C5 54.7% / 27.8%. C6 15.2% / 7.6%.
  Aggregate: 56.7% of postings evaluable by at least one rule (was falsely 100% under the
  old mixed definition); mean 0.88 of 6 rules evaluable per posting (was falsely 3.35).

- **What I gave up:** A same-day number for C2, and the comfortable but false impression
  that E4 covers nearly all postings. The honest picture is that E4's practical reach is
  much thinner than the original estimate implied — a real finding, not a data-quality
  failure, and one worth stating plainly in the dissertation rather than letting the
  original estimate stand uncorrected.

- **Also fixed in the same pass:** a duplicate-count bug (the audit script printed
  `n − n_unique`, the excess count, not true group-membership — corrected in both the
  overall and per-class figures; true count is 4,762 records / 26.6% in a duplicate group,
  not 3,505) and a missingness-calculation bug (every missing value was being counted twice).

- **Revisit if:** Stage 4 builds real lexicons for C1, C3–C6 — every provisional figure above
  must be re-measured against them, not assumed to hold. Stage 4 also builds C2's first real
  evaluable-coverage measurement.

- **Self-check:** *Why is C1 fixable with a same-day regex but C2 isn't, when both looked
  like the same kind of gap at first?*

---

## 2026-08-26 — Sharpen the explainability gap from "absent" to "never tested for faithfulness"

- **Decision:** My research gap on explainability does NOT claim that explanation is absent
  from fraud detection. It claims that, where explanation is used, it is shown as a few
  examples but never tested for whether it faithfully reflects the model.

- **Options considered:**
  - (A) Keep the stronger, simpler claim: "explainability is absent from fraud detection."
  - (B) Sharpen it: explanation is rare, and where present it is never tested for faithfulness.

- **Why I chose this:** While writing Chapter 2 I read Naudé et al. (2023), a fraud-domain
  paper that actually uses LIME. That single paper disproves the "absent" claim outright. If
  I had kept option A, an examiner holding Naudé could sink the sentence in seconds. Option B
  is not a retreat — it is stronger, because it survives Naudé and because it maps exactly
  onto what I actually built: my Objective 4 tests explanation faithfulness with
  comprehensiveness and sufficiency, which is the very thing Naudé never did. The gap and my
  contribution now line up perfectly.

- **What I gave up:** A punchier one-line gap. Traded for one that cannot be knocked over.

- **Revisit if:** I find a fraud-detection paper that already runs a systematic fidelity
  evaluation of its explanations — then the gap must narrow again to whatever they did not do.

- **Self-check:** *Why can't I say explainability is absent from fraud detection, and which
  paper forces the more careful wording?*

---

## 2026-08-26 — Cut Mohiddin et al. (2025) from the reviewed literature

- **Decision:** Mohiddin et al. (2025) is not cited in my literature review and does not
  appear in my summary table.

- **Options considered:**
  - (A) Include it to raise my paper count.
  - (B) Keep it as one weighted-down sentence.
  - (C) Cut it entirely.

- **Why I chose this:** The paper has no stated dataset, no reported metrics, and no clear
  protocol, and some of its citations look unreliable. A literature review is judged partly
  on the quality of what I choose to include. Putting an evidence-free paper in the same
  summary table as Akram (IEEE Access, Q1) and Naudé (AI & Society) drags down the whole
  table's credibility. The one "future work" point it offered is made better by Akram
  anyway. Including it adds risk without adding evidence, so it goes.

- **What I gave up:** One entry on my paper count. Not worth keeping at the cost of table
  credibility.

- **Revisit if:** A later, properly reported version of the same work appears.

- **Self-check:** *On what grounds did I exclude a paper from my review, and why is excluding
  weak work a strength rather than a gap?*

---

## 2026-08-26 — Structure the research gap as four gaps derived by comparison, not lifted from papers

- **Decision:** My Chapter 2 research gap is four distinct gaps: (1) text and metadata are
  never checked for agreement — my main gap; (2) explanations are rare and never tested for
  faithfulness; (3) evaluation is not always leakage-controlled; (4) output is a binary label
  rather than a graded, calibrated score.

- **Options considered:**
  - (A) State one single gap (consistency verification) and stop.
  - (B) Derive several connected gaps that each map to one of my objectives.

- **Why I chose this:** No single paper states these gaps — they only become visible when the
  studies are compared against each other, which is exactly what a gap analysis is supposed
  to do (derive, not quote). Four gaps also give each of my objectives something in the
  literature to answer: the consistency gap → O1/O3, the faithfulness gap → O4, the leakage
  gap → O2/O5, the graded-output gap → O4. It makes the whole thesis hang together.

- **What I gave up:** A single, very sharp one-line gap. But gap (1) still carries that role;
  the other three support it rather than dilute it.

- **Revisit if:** One of the four turns out to be already solved in a paper I later read —
  then that gap is removed and the objective it fed is re-justified.

- **Self-check:** *Where did my four gaps come from, if no single paper states them — and
  which objective does each gap justify?*

---

## 2026-08-07 — Write objectives so that none of them assumes its own result

- **Decision:** My objectives say what I will *measure*, not what the measurement will
  *show*. Objective 3 now reads "quantify the extent to which it changes performance"
  instead of the earlier "achieving a measurable improvement".

- **Options considered:**
  - (A) Keep the original wording. It sounds confident and ambitious.
  - (B) Neutral wording focused on measurement.

- **Why I chose this:** I realised my original Objective 3 had written my expected result
  into the objective itself. If my multi-signal model turns out not to beat the baseline,
  then under the old wording I would have failed my own objective — even if I did
  everything else correctly. That felt wrong to me. A negative result is still a real
  result: finding that consistency features don't help would be useful knowledge and I
  could report it honestly. So I should not set myself up so that good work can look like
  failure. An objective is a promise about what I will investigate, not a prediction of
  what I will find.

- **What I gave up:** Wording that sounds more impressive to someone skimming the document.

- **Revisit if:** Never. This is a correctness issue, not a matter of taste.

- **Self-check:** *Why is "achieving an improvement" a bad way to word a research objective?*

---

## 2026-08-07 — Use four evidence categories for measurement, not five

- **Decision:** The taxonomy I actually measure has four categories — E1 text/content cues,
  E2 identity and contact cues, E3 metadata completeness, E4 text–metadata consistency. The
  external company-presence check still exists inside my API as a supporting qualitative
  feature, but it is excluded from the ablation analysis and from all quantitative results.

- **Options considered:**
  - (A) Five categories, with external presence measured like the rest.
  - (B) Five categories, but redefine external presence as an internal "employer
    plausibility" score built from `company_profile` and `industry`.
  - (C) Four measured categories, with the external check demoted to API-only.

- **Why I chose this:** Two problems killed the first two options. First, EMSCAD has no
  separate company-name field — the only employer information is free text inside
  `company_profile` — and the postings are from 2012 to 2014. If I search the web today for
  a company mentioned in a twelve-year-old posting, whatever comes back is noise, not
  evidence. I would be measuring something meaningless and reporting it as a signal.
  Second, option B looked safer but was actually worse for my ablation: it would have used
  `company_profile`, which E2 already uses. Two categories drawing on the same field means
  I cannot separate their contributions, so my ablation numbers would be contaminated. I
  would rather have four categories I can measure cleanly than five where one is fiction.
  I still keep the external check in the artefact because it is genuinely useful to a real
  job seeker looking at a real posting today — it just doesn't belong in my results.

- **What I gave up:** A fifth category that sounded impressive in my proposal, and any
  quantitative claim I could have made about external verification.

- **Revisit if:** My Tier 2 collection works well at scale. A live external check on a
  posting from 2026 *is* meaningful, so I could report it qualitatively there.

- **Self-check:** *Why can't I evaluate the external company-presence check on EMSCAD, and
  why would folding it into E2 have damaged my ablation?*

---

## 2026-08-07 — Use class weighting for both models, not SMOTE for one and class weighting for the other

- **Decision:** Both my baseline and my improved model use class weighting, with identical
  settings, to handle the 4.8% fraud class. SMOTE stays in the project only as a clearly
  labelled extra experiment on the baseline.

- **Options considered:**
  - (A) SMOTE for both models, following Akram et al. (2024).
  - (B) SMOTE for the baseline, class weighting for the improved model — this is what my
    first draft actually said.
  - (C) Class weighting for both, SMOTE as a side experiment.

- **Why I chose this:** This is probably the most important decision in my whole design,
  and I nearly got it wrong. My entire research claim is that adding multi-signal evidence
  and consistency verification improves credibility scoring. To show that, my two models
  must differ in *only* the things I am testing. Under option B they would have differed in
  three ways at once — text representation, structured features, *and* imbalance strategy.
  If the improved model then performed better, I could not say why. Someone could ask "how
  do you know it wasn't just the different balancing?" and I would have no answer. My
  central claim would be untestable, which is worse than being wrong.

  The second reason is about my output. My headline deliverable is a *calibrated* 0 to 100
  score, not a label. SMOTE creates synthetic minority examples, which shifts the predicted
  probability distribution away from the real one. Since the meaning of my score depends on
  those probabilities being trustworthy, protecting calibration matters more to me than
  squeezing out a slightly higher F1. I keep SMOTE as a separate arm so I can still compare
  against Akram et al., but it is reported separately and never mixed into the main
  comparison.

- **What I gave up:** Direct number-for-number comparability with SMOTE-based published
  results, and possibly a little raw F1.

- **Revisit if:** Calibration turns out to be robust to SMOTE in my setting, or if the
  supplementary arm shows a large and consistent advantage I can't ignore.

- **Self-check:** *Give the two separate reasons I chose class weighting — one about
  comparison validity, one about calibration.*

---

## 2026-08-07 — Group duplicate postings before splitting the data

- **Decision:** Before splitting, I normalise the description text, compute a content hash,
  and make sure every record sharing a hash goes into the same partition.

- **Options considered:**
  - (A) Plain stratified random split, which is what my proposal said.
  - (B) Delete all duplicates.
  - (C) Group-aware split — keep the duplicates but never let a group span the boundary.

- **Why I chose this:** The dataset profile shows 17,880 records but only about 15,100
  unique descriptions, so roughly 2,700 postings repeat. Some of these are the same
  fraudulent campaign posted over and over with small changes — the "English Teacher
  Abroad" cluster is a clear example. If I split randomly, near-identical fraudulent
  postings land in both my training set and my test set. My model then doesn't learn what
  fraud looks like; it memorises specific strings and recognises them again at test time. I
  would get a high F1 that means nothing. I chose option C over option B because deleting
  duplicates changes the real class balance of the dataset, whereas grouping keeps the data
  intact and only controls where records are allowed to go.

  > ⚠️ **Correction, 2026-08-27:** the "English Teacher Abroad" example above is factually
  > wrong — measured on the real CSV, that cluster is 100% legitimate, 0% fraudulent. See
  > the correction entry dated 2026-08-27 above. The decision itself still stands, justified
  > independently by the fraud class being separately measured at 40.3% duplicated.

- **What I gave up:** Comparability with published EMSCAD results that did not control for
  this. My numbers will probably look lower than theirs. I have decided to treat that as a
  finding worth reporting rather than a problem to hide — if leakage control lowers scores,
  that says something about the published figures.

- **Revisit if:** The audit shows duplication is actually negligible. I doubt it, but the
  ~2,700 figure is an estimate from a profiler and I have not measured it myself yet.

  > ⚠️ **Update, 2026-08-27:** now measured. 4,762 records (26.6%) sit in a duplicate group
  > under exact-normalised hashing; the fraud class is disproportionately duplicated (40.3%
  > vs 25.9% for legitimate). The near-duplicate grouping *method* itself is still an open
  > decision — see Decision 0.2, resolved 2026-09-20.

- **Self-check:** *What exactly goes wrong if I use a plain random split on EMSCAD, and why
  did I group duplicates instead of deleting them?*

---

## 2026-08-07 — Use a train/validation/test split instead of 80:20

- **Decision:** Roughly 70:15:15. The validation set is used for transformer
  hyperparameters, the decision threshold, and fitting the calibrator. The test set is used
  once, at the end, for reporting.

- **Options considered:**
  - (A) 80:20 train/test, as in my proposal.
  - (B) 70:15:15 train/validation/test.
  - (C) Nested cross-validation.

- **Why I chose this:** Once I listed out everything I need to fit, the problem became
  obvious. I have to choose transformer hyperparameters, pick a decision threshold, and fit
  a probability calibrator. That is three separate things, and none of them may touch the
  test set — if they do, my final numbers are optimistic and I have no clean estimate of how
  the system performs on unseen data. With only a train/test split there is simply nowhere
  honest to fit them. Option C is more rigorous statistically, but it multiplies my compute
  and complexity, and I am one person on a laptop with a fixed deadline. A separate
  validation partition solves the actual problem at a cost I can afford.

- **What I gave up:** Some training data, and some robustness compared with nested CV.

- **Revisit if:** The fraud class in my test partition turns out too small for stable
  estimates even across three seeds.

- **Self-check:** *Name the three things I fit on the validation set, and explain why none
  of them can be fitted on the test set.*

---

## 2026-08-07 — Add an explicit probability calibration stage

- **Decision:** I fit a probability calibrator — Platt scaling or isotonic regression,
  chosen on validation performance — and map the calibrated probability to my 0 to 100
  credibility score. I report Brier score, expected calibration error, and a reliability
  curve.

- **Options considered:**
  - (A) Map the raw model probability straight to 0–100, as in my proposal.
  - (B) Fit a calibrator first, then map.

- **Why I chose this:** I noticed a gap in my own design. My training labels are binary —
  fraudulent or legitimate — but my output is a graded score, and nothing in my original
  plan connected the two. If I just rescale a raw model probability into a number between 0
  and 100, then a score of 70 doesn't actually mean anything specific; it is the model's
  uncalibrated output stretched onto a different axis. Classifiers, especially neural ones,
  are often overconfident, so those raw numbers can be badly off even when the ranking is
  good. Calibration is what makes the number defensible: after it, a score around 70 should
  correspond to roughly the right proportion of postings actually being legitimate, and I
  can test that with a reliability curve. Without this stage my main deliverable would have
  had no validation method at all.

- **What I gave up:** Pipeline simplicity — one more component that can fail or be
  misconfigured.

- **Revisit if:** Neither calibrator improves reliability over the raw probabilities. In
  that case I report that honestly and justify using the identity mapping.

- **Self-check:** *Why is a binary training label a problem for a 0–100 output, and how does
  calibration fix it?*

---

## 2026-08-07 — Test explanation quality computationally instead of asking human reviewers

- **Decision:** I evaluate my explanations using comprehensiveness and sufficiency
  (deletion and insertion tests) plus a rule-consistency check. No human participants.

- **Options considered:**
  - (A) Collect feedback from reviewers or users on whether explanations are helpful.
  - (B) Computational fidelity testing only.
  - (C) Both.

- **Why I chose this:** There was a practical reason and a better reason. The practical one
  is that involving human participants means a participant ethics application plus
  recruitment, scheduling and analysis, and I don't have room for that in my remaining
  timeline. The better reason is what each approach actually tests. Asking people whether an
  explanation *feels* helpful tells me about presentation. Fidelity testing tells me whether
  the explanation reflects what the model actually did. That second property is the one that
  matters for safety: an explanation that sounds convincing but doesn't match the model's
  real reasoning is worse than giving no explanation at all, because it makes the user
  confident for the wrong reasons. Fidelity testing is also quantitative and reproducible,
  which suits a dissertation better than a small unrepresentative user study would.

- **What I gave up:** Any evidence about whether real job seekers find my explanations
  *useful*. That is a genuine limitation and I state it as one rather than pretending
  fidelity testing covers it.

- **Revisit if:** My timeline opens up and ethics approval turns out to be quick. A small
  supervised usability round would strengthen Objective 4.

- **Self-check:** *Why is a plausible-but-unfaithful explanation worse than no explanation?*

---

## 2026-08-07 — Keep EMSCAD and add a small contemporary validation set (two-tier strategy)

- **Decision:** EMSCAD is Tier 1 and does all my training, tuning and benchmarking. A small
  independently collected set of 300 to 600 contemporary postings is Tier 2 and is used only
  as a held-out temporal validation set. The two are never merged.

- **Options considered:**
  - (A) EMSCAD only.
  - (B) Replace EMSCAD with a modern scraped dataset.
  - (C) Merge modern data into EMSCAD and train on everything.
  - (D) Two tiers, kept separate.

- **Why I chose this:** EMSCAD is from 2012 to 2014, and it is now 2026. Fraud has changed a
  lot in that time — in particular, scammers now use language models to write postings,
  which removes the bad grammar and clumsy phrasing that older detectors relied on. So
  option A would leave me with an artefact demonstrably tuned to a job market that no longer
  exists. But I couldn't take option B either, because EMSCAD is the benchmark every paper
  in my literature review uses; if I drop it, I lose the ability to compare my results with
  anyone. Option C is worse than both — mixing eras contaminates the benchmark and makes my
  numbers uninterpretable, since I could never tell which era drove a result. Option D gives
  me both things at once: full comparability with the literature on Tier 1, and a temporal
  generalisability result on Tier 2 that, as far as I can see, no paper in my review has
  produced. That turns my dataset's biggest weakness into a contribution.

  > ✅ **Reaffirmed, 2026-08-27** after checking four externally-suggested alternative
  > "second datasets" against their primary sources — all four turned out to be EMSCAD
  > derivatives. See the decision entry dated 2026-08-27 above. This decision was not
  > weakened by that check; if anything it is more clearly correct now.

- **What I gave up:** Time. Tier 2 collection is my slowest task and my main schedule risk,
  especially the fraudulent side. I also have limited statistical power on Tier 2 because
  the sample is small, so I report confidence intervals there.

- **Revisit if:** Collecting the fraudulent side proves impossible in the time I have. My
  fallback is to report Tier 2 qualitatively and state the limitation openly.

  > ⚠️ **Status, 2026-10-06:** the fallback clause is now time-boxed to a single day — see
  > the 2026-10-06 entry at the top of this file.

  > ✅ **Status, 2026-10-07:** fallback not needed — both tiers of Tier 2 met their targets
  > within Day 1. See the 2026-10-07 entries above.

- **Self-check:** *Why didn't I just replace EMSCAD with modern data, and why can't I merge
  the two tiers?*

---

## 2026-08-07 — Label Tier 2 by where the data came from, and test for source leakage

- **Decision:** Legitimate postings come from employers' own applicant tracking system
  endpoints and official public job feeds — legitimate by construction. Fraudulent postings
  come from documented scam repositories and advisories, and only where the original posting
  text is reproduced. I also train a classifier to predict the *source* rather than the
  label, and report what it scores.

- **Options considered:**
  - (A) Collect postings and annotate them myself.
  - (B) Label by provenance.
  - (C) Label by provenance without any leakage check.

- **Why I chose this:** Option A isn't realistic. For a genuinely ambiguous posting I have
  no way to establish ground truth on my own authority — I would just be guessing, and my
  guesses would become my labels, which is circular. Provenance labelling removes my
  judgement from the process entirely: if a posting came from a company's own Greenhouse
  board it is legitimate by definition, and if a consumer protection body has documented it
  as a scam then it is fraudulent by report.

  But provenance labelling brings a serious danger of its own, which is why I rejected
  option C. If all my legitimate postings come from one kind of source and all my fraudulent
  ones from another, my model can learn to recognise the *source formatting* rather than
  fraud, and it would score brilliantly while meaning absolutely nothing. That failure is
  invisible in normal metrics — it looks like success. The source probe is how I detect it,
  so it isn't optional. I also normalise aggressively and exclude features whose
  availability differs systematically by source.

  > ✅ **Applied, 2026-10-07:** the fraud-side BBB-sourced records are labelled
  > "fraudulent by report," not independently fact-checked for whether the underlying
  > narrative is literally true — consistent with this decision. The quoted scammer
  > message/email itself is what I train/evaluate on, not the surrounding narrative, which
  > keeps the labelling principle intact (the text is reproduced, not paraphrased by the
  > reporter or by me).

- **What I gave up:** Coverage of borderline cases. My Tier 2 set will contain clearer
  examples than the real world does, which probably makes it an optimistic test. I say so.

- **Revisit if:** The source probe scores near-perfect even after normalisation. Then I
  restrict Tier 2 to text-only features, or report it qualitatively.

- **Self-check:** *What is source leakage, why would it be invisible in my normal metrics,
  and how does the probe catch it?*

---

## 2026-08-07 — Drop the `in_balanced_dataset` column entirely

- **Decision:** I exclude it from the feature space completely.

- **Options considered:**
  - (A) Keep it as a feature.
  - (B) Drop it.

- **Why I chose this:** This column marks whether a record was included in the dataset
  authors' own pre-built balanced subset. That is information about how the dataset was
  assembled — it says nothing whatsoever about the job posting itself. A real job seeker
  looking at a real vacancy would never have access to anything like it. Including it would
  let my model pick up on an artefact of dataset construction, which is straightforward
  leakage, and any performance it bought me would be fake.

- **What I gave up:** Nothing of value.

- **Revisit if:** Never.

- **Self-check:** *What does `in_balanced_dataset` actually describe, and why does that make
  it leakage?*

---

## 2026-08-07 — Extract contact and media tokens before stripping HTML

- **Decision:** My preprocessing order is: first count `#EMAIL_#`, `#PHONE_#` and `#URL_#`
  tokens along with image references and link counts, *then* strip the markup.

- **Options considered:**
  - (A) Strip HTML first, which is the conventional order in most tutorials.
  - (B) Extract first, then strip.

- **Why I chose this:** When EMSCAD was anonymised, contact details weren't deleted — they
  were replaced with hashed placeholder tokens that are still sitting inside the description
  text. Those tokens are the basis of my whole E2 identity and contact category: whether a
  posting pushes the applicant to email or phone directly, instead of applying through the
  platform, is a real fraud signal. If I strip markup first, those tokens go with it and I
  destroy an entire evidence category before I have even computed it — and worse, I would
  probably not notice, because the pipeline would still run and just produce zeros.

- **What I gave up:** Nothing. This is an ordering constraint, not a trade-off.

- **Revisit if:** Never.

- **Note to self:** The email *domain* cannot be recovered, because hashing destroys it.
  That means I cannot reproduce Goud and Reddy's free-webmail-domain feature on EMSCAD. I
  document this as a dataset limitation rather than quietly leaving it out.

- **Self-check:** *What breaks if I strip HTML first, and why wouldn't I notice?*

---

## 2026-08-07 — Make raw text the primary API input, with URL support best-effort only

- **Decision:** My `/score` endpoint takes raw posting text as its main input path. URL
  ingestion is secondary and only supported for sources that permit automated retrieval.

- **Options considered:**
  - (A) URL-first, as described in my proposal.
  - (B) Text-first, URL optional.

- **Why I chose this:** My proposal assumed a user would paste a LinkedIn or Indeed link and
  the system would fetch it. There are two problems with that. Automated retrieval from the
  major recruitment platforms breaches their terms of service, which I should not be
  building a university project on. And technically it is fragile — page structures change
  without warning and scrapers break constantly. If my primary input path depends on that,
  then my entire deliverable can stop working for reasons that have nothing to do with my
  research. Raw text always works, requires no permission, and keeps the artefact stable.

- **What I gave up:** Convenience for the end user, which was honestly part of the original
  appeal of the idea.

- **Revisit if:** A sanctioned API route to posting content becomes available.

- **Self-check:** *Give the two reasons — one legal, one technical — that URL input isn't my
  primary path.*

---

# Pending decisions (not yet made)

> ✅ **Resolved:** the 2026-09-20 scope-cut round, Decision 0.2, the 2026-10-06 sprint
> compression (deadline, Tier 2 time-boxing, ablation contingency, triage order), Decisions
> 0.3 and 0.4 (resolved 2026-10-06, 23:50), and Tier 2 fraud-side sourcing (resolved
> 2026-10-07, 17:30) are all closed. Two items remain genuinely open:

## Success thresholds for each objective

- **The question:** What actually counts as success for each objective? Still unset in
  `methodology.md`.
- **Constraint:** Agree with supervisor before results are seen, if any contact window
  exists this week. If not, state in Chapter 5 that thresholds were self-set under time
  pressure.

## Tier 2 ethics approval status

- **The question:** Has the institutional ethics application for Tier 2 primary data
  collection actually been submitted?
- **Status, 2026-10-06:** explicitly not gating collection this week (see the 2026-10-06
  entry above). This remains open and must be named as a limitation in Chapter 6.
