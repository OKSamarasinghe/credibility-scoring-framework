# sources.md — Verified Claims & References

_Last updated: 2026-10-07_

> **The rule:** every claim, definition, statistic or method that came from an AI model goes
> here until I have checked it against a **primary** source. Anything still marked
> `Verified: NO` must **not** appear in my dissertation as fact.
>
> **Status key:** ❌ unverified · ⚠️ partially evidenced, needs primary confirmation ·
> ✅ verified against primary source · 🟡 measured but PROVISIONAL (see item note)
>
> **Priority order:** items in Part A are already sitting inside my finalised documents.
> Those are the urgent ones.

---

# PART A — Unverified claims already inside my documents

## 1. ❌ Full reference — Hevner et al. (2004), Design Science Research

- **Claim:** DSR as a research paradigm, cited in `Research_Methodology_Final.docx` §1.
- **From:** AI model, 2026-08-07. Given from memory, not retrieved.
- **Verified:** NO
- **Need:** Full reference — authors, year, title, journal, volume, pages. Likely *MIS
  Quarterly*, but **confirm**; do not cite from memory.
- **Action:** Retrieve via Google Scholar / library. Read at least the abstract and the
  design-science guidelines section.

## 2. ❌ Full reference — Peffers et al. (2007), DSR Methodology (the six steps)

- **Claim:** The six-activity DSR process model underpinning my whole methodology structure.
- **From:** AI model, 2026-08-07; also referenced in the supervisor's field guide.
- **Verified:** NO
- **Need:** Full reference — likely *Journal of Management Information Systems*, **confirm**.
- **Action:** Retrieve and read. This is the backbone of my methodology chapter — I must be
  able to name the six activities and explain why my nine stages map onto them.

## 3. 🟡 Consistency rule coverage C1–C6 — MEASURED 2026-08-27, but PARTIALLY and PROVISIONALLY

- **Claim:** Per-rule field coverage AND evaluable coverage for C1–C6, for
  `Research_Methodology_Final.docx` §3.1.
- **Original claim (now superseded):** field coverage C1 100%, C2 98%, C3 81%, C4 61%,
  C5 55%, C6 16% — AI model, 2026-08-07, derived by inference, not measured. **This
  estimate is now replaced by the measured figures below.**
- **Measured field coverage (2026-08-27, real CSV, n = 17,880):**

  | Rule | Field coverage (measured) | Was estimated |
  |---|---|---|
  | C1 Remote/on-site | 100.0% | 100% |
  | C2 Location mismatch | 88.4% | 98% |
  | C3 Employment type | 80.6% | 81% |
  | C4 Experience level | 60.6% | 61% |
  | C5 Education | 54.7% | 55% |
  | C6 Salary | 15.2% | 16% |

  **Field coverage is VERIFIED** — directly measured on the real CSV, reproduced
  identically across two independent environments.

- **Measured evaluable coverage (2026-08-27) — the honest number for the methodology
  table, but NOT yet fully verified:**

  | Rule | Evaluable coverage | Status |
  |---|---|---|
  | C1 | 10.5% | 🟡 PROVISIONAL — placeholder pattern (see note below) |
  | C2 | **not measured** | ❌ DEFERRED to Stage 4 — see note below |
  | C3 | 12.2% | 🟡 PROVISIONAL |
  | C4 | 30.2% | 🟡 PROVISIONAL |
  | C5 | 27.8% | 🟡 PROVISIONAL |
  | C6 | 7.6% | 🟡 PROVISIONAL |

  Aggregate: **postings evaluable by at least one rule: 10,145 (56.7%)**; mean rules
  evaluable per posting: **0.88 of 6**. An earlier draft of this audit used an inconsistent
  definition of "evaluable" (loose for C1–C3, strict for C4–C6) and reported false figures
  of 100% and 3.35 — corrected 2026-08-27, see `decisions.md` (Decision 0.1).

- **Why "provisional" (C1, C3–C6):** these five figures use the *audit script's own*
  placeholder pattern-matching (regexes for remote/on-site language, employment-arrangement
  language, "N years," education words, money words) — not the final Stage 4 lexicons.
  They must be **re-measured once Stage 4 lexicons are frozen**, and may change.

- **Why C2 has no evaluable figure at all:** C2's premise is that a place name in the free
  text differs from the structured `location` field — genuine location extraction, an
  open-vocabulary problem that cannot be honestly approximated with a quick regex (unlike
  C1/C3, whose vocabularies are small and enumerable). Building a placeholder regex for it
  now would create a second, weaker implementation of the rule that would disagree with the
  real Stage 4 matcher. Field coverage (88.4%) is reported as an explicit **upper bound**
  only. Decision logged in `decisions.md`, 2026-08-27.
- **Verified:** Field coverage — YES. Evaluable coverage — PARTIAL (C1, C3–C6 provisional;
  C2 not measured). **Do not mark this item fully verified.**
- **Action:** Re-measure C1, C3–C6 evaluable coverage against final Stage 4 lexicons before
  they enter the dissertation as final figures. Build C2's real location-matching logic in
  Stage 4, then measure it for the first time — do not backfill a proxy.

## 4. ✅ Boolean fields stored as string literals `'t'` / `'f'`

- **Claim:** In the EMSCAD CSV, `telecommuting`, `has_company_logo`, `has_questions`,
  `fraudulent` and `in_balanced_dataset` are strings, not booleans. Stated as fact in
  `Research_Methodology_Final.docx` §2.1.2.
- **Verified:** YES — confirmed directly on the real CSV (`DataSet.csv`, 17,880 × 18), via
  `emscad_audit_fixed.py`, 2026-08-27. All five boolean columns contain only the literals
  `t` and `f`, zero nulls. **Reproduced identically in two independent environments**
  (sandbox pandas, and the project venv on pandas 3.0.5) — same result both times, so the
  pandas major-version difference does not affect this measurement.
- **Action:** none — closed. §2.1.2 is correct as written.

## 5. ✅ Duplicate and near-duplicate postings — MEASURED 2026-08-27 (corrected same day)

- **Claim:** Roughly 2,700 duplicate/near-duplicate postings; used to justify the
  group-aware split.
- **Measured (normalised-exact hashing — HTML/markup stripped, anonymisation tokens
  stripped, lowercased, non-alphanumeric stripped, then MD5 on `description`):**
  - Unique descriptions, exact raw string match: 15,095
  - Unique descriptions, normalised: 14,375
  - **Records sitting in a duplicate group (size > 1): 4,762 (26.6% of the corpus)**
  - Duplicate groups (size > 1): 1,257; largest group: 417 records
  - Fraudulent records in a duplicate group: **349 of 866 (40.3%)**
  - Legitimate records in a duplicate group: **4,412 of 17,014 (25.9%)**
- **Correction, logged 2026-08-27:** the audit script originally printed a figure that was
  `n − n_unique` — the *excess* count, not the number of records actually sitting in a group
  of size > 1. Corrected in both the overall and per-class figures; the true group-membership
  figures above are the ones to use everywhere.
- **Correction, logged 2026-08-27, independently corroborated 2026-08-27:** `decisions.md`'s
  justifying example for the group-aware split ("English Teacher Abroad" cluster) was
  factually wrong — that cluster (715 records under a looser text-prefix match, largest
  exact-normalised group 417) is **100% legitimate, 0% fraudulent**, not a fraud campaign as
  originally stated. Independently corroborated by a completely different source: the
  Internship-Job-Scam-Dataset (Hugging Face), which derives from the same underlying EMSCAD
  data and shows `original_fraudulent: 0` for the same cluster. The decision to group-aware
  split still stands (justified independently by the fraud class being 40.3% duplicated),
  but the example sentence in `decisions.md` has been corrected (as an appended note, not a
  silent edit — see `decisions.md`, 2026-08-27).
- **Open — near-duplicate grouping method (Decision 0.2, still pending):** MD5-on-normalised-
  text catches only *exact*-after-normalisation duplicates, not genuine near-duplicates.
  Demonstrated: the "English Teacher Abroad" campaign (715 records sharing a distinctive
  opening phrase) fragments across 15 separate MD5 groups. A cheap proxy (hash of the first
  12 normalised tokens) was tested for comparison only, not adopted — merges 48.9% of the
  corpus, likely over-merging unrelated postings. **This decision is not yet made.**
- **Verified:** YES for the figures reported above, under the normalised-exact-hash
  definition, explicitly labelled as such.

## 6. ❌ `has_company_logo` may be a dataset artefact rather than a durable fraud signal

- **Claim:** Justifies my targeted ablation in `Research_Methodology_Final.docx` §9.2.
- **From:** AI model, 2026-08-07, from general knowledge. No source given.
- **Verified:** NO
- **Action:** Check whether any published EMSCAD study discusses this. If none does, I must
  reword the methodology to present it as **my own hypothesis motivating the ablation**,
  not as an established concern. Currently it reads as established.

## 7. ✅ EMSCAD anonymisation uses hashed placeholder tokens (`#URL_…#`, `#EMAIL_…#`, `#PHONE_…#`)

- **Claim:** Underpins my entire E2 identity/contact feature group.
- **Verified:** YES — measured directly on the real CSV, 2026-08-27. All three token types
  present and discoverable (no other placeholder token types exist in the corpus):
  - `#URL_#`: 7,362 postings (41.2%), 23,270 total occurrences
  - `#EMAIL_#`: 1,377 postings (7.7%), 2,368 total occurrences
  - `#PHONE_#`: 657 postings (3.7%), 1,026 total occurrences
  - Token presence by class (descriptive only, not a modelling result): `#EMAIL_#` appears
    in 20.1% of fraudulent postings vs 7.1% of legitimate (ratio 2.84); `#PHONE_#` 9.2% vs
    3.4% (ratio 2.72); `#URL_#` 42.4% vs 41.1% (ratio 1.03, i.e. not discriminative).
  - E2 stands as designed. This was the single highest-impact unknown in the whole audit —
    had EMAIL/PHONE tokens been absent, E2 would have needed redesigning.
- **Action:** none — closed.

## 8. ❌ Full reference — Venable, Pries-Heje & Baskerville, FEDS framework

- **Claim:** Evaluation strategy positioning (ex ante/ex post, artificial/naturalistic) in
  `methodology.md`.
- **From:** Supervisor's field guide + AI model, 2026-08-07.
- **Verified:** NO
- **Action:** Retrieve full reference. Confirm the two axes are named as I have used them.
  (Note: `Research_Thesis_Draft.md` cites this as Venable, Pries-Heje & Baskerville, 2016,
  *European Journal of Information Systems*, 25(1), 77–89 — this needs independent
  confirmation before treating it as settled, since it entered the thesis draft the same way
  every other unverified claim did.)

## 9. ✅ EMSCAD composition — 17,880 total; 17,014 legitimate; 866 fraudulent; 2012–2014

- **Verified:** YES — measured directly, 2026-08-27. 866 fraudulent (4.84%), 17,014
  legitimate (95.16%), 17,880 total, 18 columns. Matches the expected published figures
  exactly. Confirmed the file is the original EMSCAD structure (no `job_id` column, so not
  the reduced Kaggle `fake_job_postings.csv` derivative).
- **Action:** none — closed. The 2012–2014 date range itself is not independently
  re-verified here; low risk, well corroborated across the literature and independently
  corroborated again on 2026-08-27 via the DIFrauD dataset card (see item #19).

---

# PART B — Claims used in reasoning, not yet in documents

## 10. ❌ FTC: job/employment scam reports nearly tripled since 2020; losses from ~$90m to $500m+ annually

- **From:** AI web search, 2026-08-07. **Secondary reporting** (news/commentary sites), not
  the FTC itself.
- **Verified:** NO
- **Status note:** superseded in practice by Part C item C2 (FTC 2025 press release, primary
  source) for the Chapter 1 draft. Retained here for traceability only.

## 11. ❌ BBB: employment scam reports doubled in 2025

- **From:** AI web search, 2026-08-07. Secondary reporting of a BBB study.
- **Verified:** NO
- **Status note:** NOT used in the final Chapter 1 draft. If reintroduced, re-verify.

## 12. ❌ AI-generated postings have eroded lexical fraud cues (grammar, spelling, generic phrasing)

- **From:** AI web search, 2026-08-07 — commercial/commentary sources, not peer-reviewed.
- **Verified:** NO
- **Importance:** **This is the central motivation for my Tier 2 work and the signal-durability
  hypothesis.** It currently rests on non-academic sources.
- **Action:** Find peer-reviewed support, or an authoritative body (FBI IC3, ITRC). If no
  strong source exists, present it explicitly as **my hypothesis to be tested by Tier 2
  experiment T2 (signal durability)**, not as established fact. That is defensible;
  asserting it is not.

## 13. ❌ Task-based scams as a distinct contemporary typology

- **From:** AI web search, 2026-08-07 (security-vendor report + BBB commentary).
- **Verified:** NO
- **Action:** Verify against primary reporting before including in the taxonomy extension.
  **Note, 2026-10-07:** the Tier 2 fraud-side BBB collection (item #20 below) independently
  surfaces several genuine task-based scam reports (e.g. Scam IDs 1160023, 808306) during
  sourcing, which may be useful primary-ish supporting evidence that this typology exists in
  current reports — but a BBB consumer report is still not a peer-reviewed source; treat as
  illustrative, not as the needed verification.

## 14. ✅ Free job-board API availability (Greenhouse, Lever, USAJOBS, Arbeitnow, Adzuna free tier); Indeed Publisher API retired 2023

- **Verified:** YES, 2026-09-20, checked against each provider's own documentation.
  - **Greenhouse Job Board API** — genuinely public, no authentication, no API key.
    `boards-api.greenhouse.io/v1/boards/{company-slug}/jobs`. Returns title, location,
    department, full description, salary when the employer discloses it. Best schema match
    to EMSCAD. Requires knowing company board tokens in advance — no open cross-company
    search endpoint.
  - **Lever Postings API** — genuinely public, no authentication, no API key.
    `api.lever.co/v0/postings/{site}`. Same field richness and same limitation (need site
    slugs in advance).
  - **USAJOBS API** — free, real access via a quickly-issued email-registered key, official
    US government (OPM). Standard acceptable-use terms (no malicious use, no impersonation).
    **Scope limitation:** federal civil-service postings only, using federal pay-grade/
    occupational-series conventions rather than commercial fields — a real representativeness
    concern if relied on heavily for Tier 2, since it won't resemble EMSCAD's commercial
    job-posting schema as closely as Greenhouse/Lever.
  - **Arbeitnow API** — free, no authentication required, aggregates from multiple ATS
    sources, EU/remote-leaning coverage.
  - **Adzuna API** — free tier via an instantly-issued App ID/Key, rate-limited (hundreds of
    calls/day) but real; title, company, location, salary, description across ~20 countries.
  - **Indeed Publisher API** — confirmed still retired (deprecated 2023); current official
    APIs are employer-side/partner-gated only. Original claim independently reconfirmed.
- **Note:** several search results surfaced paid third-party scraping services built on top
  of these free APIs. Not used — `project.md`'s "no paid data sources" constraint means going
  directly to the official free endpoints listed above.
- **Action:** none remaining — closed. Practical next step is building a company-slug list
  for Greenhouse/Lever querying, which is Tier 2 collection work, not verification work.

## 15. ❌ SMOTE distorts predicted probabilities / harms calibration

- **Claim:** A load-bearing justification for choosing class weighting (`decisions.md`).
- **From:** AI model, 2026-08-07. No source given.
- **Verified:** NO
- **Action:** Find a citable source on oversampling and probability calibration. If I cannot
  support it, I can still justify the choice on **comparison-validity** grounds alone (the
  confound argument), which needs no citation — but I should know which leg I am standing on.

## 16. ❌ Comprehensiveness / sufficiency as explanation-fidelity metrics

- **From:** AI model, 2026-08-07. These come from the XAI/NLP evaluation literature (I
  believe associated with the ERASER benchmark) but **no reference was given**.
- **Verified:** NO
- **Action:** Find the originating paper and cite it. I cannot use metrics in O4 whose
  definition I cannot attribute.

## 17. ❌ All numeric values in `Framework_Explanation_Walkthrough.docx` are illustrative

- **Claim:** Credibility score 13; baseline F1 0.71 and improved F1 0.79; Brier 0.061 → 0.048;
  ablation costs 0.05 (E1) and 0.07 (E4); taxonomy audit agreement 94 of 100.
- **From:** AI model, 2026-08-07, as a **worked example** demonstrating how each component
  behaves. Not derived from any data.
- **Verified:** NO — and they never will be, because they are not measurements.
- **Checked, 2026-08-27:** confirmed these numbers do not appear anywhere in
  `Research_Thesis_Draft.md`'s Chapters 1–3. Good — the discipline has held so far.
- **Action:** **Never cite any of them.** Delete this entry only once genuine measured
  values exist and have replaced them.

## 18. ❌ Software environment package licences (Python, pandas, scikit-learn, PyTorch, Transformers, FastAPI, SHAP, LIME) are free/open-source

- **Claim:** Made when recommending the tech stack, 2026-08-26 — licence names (PSF, BSD-3,
  Apache 2.0, MIT) given from general/training knowledge.
- **From:** AI model, 2026-08-26. Not verified against each project's actual current licence.
- **Verified:** NO
- **Action:** If licensing terms go anywhere near the dissertation, confirm each licence
  against its own repository, not from memory.

## 19. ✅ Two unattributed PDF reports recommending "second datasets" — claims checked and found unreliable

- **Claim:** Two PDF reports (no named authors, no institutional affiliation) recommended a
  "2026 Kaggle Fake Job Posting Detection competition," DIFrauD's Job Scams domain, the
  Internship-Job-Scam-Dataset, and ScamShield as suitable contemporary "second datasets" for
  this project. One of these (DIFrauD) was also suggested directly by my supervisor.
- **From:** Uploaded PDFs, 2026-08-27; supervisor conversation.
- **Verified:** YES, checked against primary sources, 2026-08-27 — **and found to
  misrepresent the data.** All four trace back to EMSCAD:
  - The Kaggle competition page (kaggle.com/competitions/fake-job-posting) and a real
    submission's GitHub repo confirm it is a Cardiff Metropolitan University Computational
    Intelligence module assignment — 12,001 rows, 18 columns, 19.4:1 class ratio matching
    EMSCAD, citing Vidros et al. (2017) directly.
  - DIFrauD's own dataset card (huggingface.co/datasets/difraud/difraud) states: "The
    Employment Scam Aegean Dataset, henceforth referred to as the Job Scams dataset..." —
    it is EMSCAD, cleaned to 14,295 records, with all structured metadata discarded.
  - The Internship-Job-Scam-Dataset's card states it was "adopted from... EMSCAD." Its
    "suspicious" class is partly built from relabelled legitimate EMSCAD text.
  - ScamShield's card lists EMSCAD as its job-data source, mixed with SMS spam data and
    ~255 LLM-generated synthetic examples.
  - DIFrauD itself is a genuine, real, peer-reviewed benchmark (Boumber, Qachfar & Verma,
    LREC-COLING 2024) — the paper is real and citable. Its *Job Scams* component specifically
    is what fails to serve as an independent Tier 2, not the paper as a whole.
- **Decision recorded:** `decisions.md`, 2026-08-27 — all four rejected as Tier 2 candidates;
  original independently-collected Tier 2 plan reaffirmed.
- **Action:** none — closed, but keep this as a standing example of why secondary reports
  must be checked against primary sources before being acted on, even when a supervisor
  forwards them.

## 20. ✅ Tier 2 fraud-side postings — 24 collected from BBB Scam Tracker, provenance verified, 2026-10-07

- **Claim:** 24 fraud-side Tier 2 records in `data/raw/tier2/tier2_fraud_raw.jsonl`, each
  one a BBB Scam Tracker consumer report containing genuinely reproduced posting-adjacent
  text (a quoted scammer email, SMS, or chat message naming a role, pay, duties, or an
  application step).
- **From:** Direct reading of BBB Scam Tracker's "employment" search (bbb.org/scamtracker),
  pages 1–8 (`from=0` to `from=70`), via Claude in Chrome driving a real, signed-in Chrome
  session, 2026-10-07.
- **Verified:** YES, in the specific sense that matters for provenance labelling — each
  record's `source_url` (`https://www.bbb.org/scamtracker/lookupscam/<id>`) was confirmed by
  reading the live page's own DOM attributes (`aria-labelledby="result-<id>-title"` linking
  each result's anchor to its title), not guessed or constructed from a pattern. The
  underlying *narrative* each report tells is **NOT independently fact-checked** — per the
  2026-08-07 "label by provenance" decision, these are labelled **fraudulent by report**
  (BBB received and published them as scam reports), not fraudulent-and-independently-
  confirmed. This is the same epistemic status EMSCAD's own fraud labels have (self-reported/
  platform-flagged, not court-adjudicated), so it is not a new or unusual weakness.
- **What was explicitly rejected during collection, and why (methodological filter, not an
  arbitrary cut):** reports with no quoted posting/ad text at all (pure narrative, e.g. "they
  called and asked if I could hear them") — these don't contain a posting-equivalent
  artefact to score; one report whose message text was obfuscated with stray `?` characters
  past the point of being legible as English.
- **Data-quality finding (log this in Chapter 6 limitations, not just here):** the identical
  "David Smith / Sheriff Gossling" check-fraud narrative appears verbatim under at least
  three distinct BBB Scam IDs (442452, 442451, and one seen on an earlier page but not
  captured) — BBB's database contains genuine near-duplicate/re-filed reports. This report
  was excluded from the 24 regardless (no quoted ad text), but the pattern means any BBB
  aggregate statistic I might later quote would need deduplication first; I am not computing
  or citing any such aggregate, so this doesn't block anything, but it belongs in the
  limitations section as a property of the source.
- **Action:** none remaining for the collection step itself — closed. Still open: this data
  has not yet been run through Stage 4 (E1–E4 extraction) or the source-probe leakage test
  (2026-08-07 decision) — that happens on Day 2+, same as the legitimate-side data.

---

# PART C — Sources cited in Chapters 1 and 2 (verification ledger)

> Every source below is ALREADY CITED in my drafted thesis (Ch 1 and/or Ch 2). Before final
> submission each must be (a) confirmed for full APA detail via MyBib, (b) read at least in
> the parts I rely on, and (c) checked for a journal ranking (Scopus/WoS/ABDC — one is enough).
>
> "Read?" = have I read the actual paper, not a snippet or another paper's summary of it?

| # | Reference | Ch | Ranking | APA confirmed? | Read? | Notes |
|---|---|---|---|---|---|---|
| C1 | Vidros et al. (2017). Automatic Detection of Online Recruitment Frauds. *Future Internet*, 9(1), 6. DOI 10.3390/fi9010006 | 1,2 | Scopus Q2 ✅ | [ ] | ❌ **via others** | Dataset origin — MUST read directly; cited only generally, no specific numbers |
| C2 | Federal Trade Commission (2025). *New FTC Data… $12.5 Billion in 2024.* | 1 | Gov primary ✅ | [ ] | ⚠️ press release read, not the Data Book | Replaces old #10/#11 secondary-reporting problem — now a primary FTC source |
| C3 | Mahbub, Pardede & Kayes (2022). Contextual Features in Australian Job Industries. *IEEE Access*, 10, 82776–82787. | 1 | Scopus Q1 ✅ | [ ] | ❌ | Pre-2023; justified as foundational |
| C4 | Vo et al. (2021). Class Imbalance in Detection of Fake Job Descriptions. *CMC*, 68(1), 521–535. | 1 | Scopus Q2 ✅ | [ ] | ❌ | Pre-2023 |
| C5 | Nanath & Olney (2023). Crowdsourcing Methods… ORF. *IJIM Data Insights*, 3(1), 100167. | 1 | Scopus ✅ | [ ] | ❌ | |
| C6 | Sullivan & Weger (2025). Transparency and Explainability in AI-Assisted Decision Making. *Proceedings of the HFES Annual Meeting*, 69(1), 1827–1833. | 1 | ⚠️ **CONFIRM** | [ ] | ❌ | Full citation now in `Research_Thesis_Draft.md` references — ranking still not verified |
| C7 | Kapoor & Narayanan (2023). Leakage and the Reproducibility Crisis… *Patterns*, 4(9), 100804. | 1 | Scopus Q1 ✅ | [ ] | ⚠️ read abstract + leakage taxonomy | Backs leakage-control design; read the taxonomy section |
| C8 | Tang et al. (2025). Explainable person–job recommendations. *Frontiers in AI*, 8, 1660548. | 1,2 | Scopus ✅ (confirm quartile) | [ ] | ✅ read in full | |
| C9 | Taneja, Vashishtha & Ratnoo (2025). Fraud-BERT. *Discover Computing*, 28(9). | 2 | Scopus ✅ (confirm quartile) | [ ] | ✅ read in full | Closest competitor; discards metadata — foils my gap |
| C10 | Akram et al. (2024). ORF Detection Using Deep Learning Approaches. *IEEE Access*, 12, 111862–111876. | 2 | Scopus Q1 ✅ | [ ] | ✅ read in full | 10× SMOTE study |
| C11 | Mehboob & Malik (2021). Smart Fraud Detection Framework for Job Recruitments. *Arab. J. Sci. Eng.*, 46(4), 3067–3078. | 2 | Scopus Q2 ✅ | [ ] | ⚠️ **snippets only** | Read full paper before submitting |
| C12 | Naudé, Adebayo & Nanda (2023). ML approach to detecting fraudulent job types. *AI & Society*, 38, 1013–1024. | 2 | Scopus ✅ (confirm) | [ ] | ✅ read in full | Fraud-domain LIME user — the reason my gap says "never tested for faithfulness" not "absent" |
| C13 | Armal et al. (2026). Fake Job Post Prediction System… *IJSRED*, 9(2), 1842–1850. | 2 | ⚠️ **likely UNRANKED** | [ ] | ✅ read (via notes) | If IJSRED has no ranking, keep as minor example only; be ready to defend |

**Second-hand rule:** studies known only through my six papers (Alghamdi, Lal, Dutta,
Nasser, Chiraratanasopa, etc.) must be cited as "as reported by [author]" or not at all.
Never inherit another paper's reference list as my own reading.

**Known issue to fix:** proposal §1.1 cites "Armal et al., 2024" but the reference list says
2026. Also "IEE Access" appears where "IEEE Access" is correct.

**Retired from Part B:** old items #10 (FTC via secondary reporting) and #11 (BBB doubled)
are superseded — the FTC claim is now sourced to the FTC press release directly (C2). The
BBB "doubled in 2025" claim was NOT used in the final Chapter 1 draft; if reintroduced,
re-log it and find the primary BBB study.

**Dropped from review:** Mohiddin et al. (2025) [old L7] and Ullah & Jamjoom (2023) [old L4]
and Goud & Reddy (2025) [old L6] are NOT cited in the current Ch 1–2 drafts. Goud & Reddy
may still be cited later for the email-domain point (decisions.md). Mohiddin was deliberately
cut from the literature review (no dataset, no metrics — viva liability).

---

# PART D — References I still need to find

| Need | For | Found? |
|---|---|---|
| SHAP originating paper (Lundberg & Lee) | O4 method attribution | [ ] |
| LIME originating paper (Ribeiro et al.) | O4 method attribution | [ ] |
| DistilBERT paper (Sanh et al.) | O3 model justification | [ ] |
| SMOTE paper (Chawla et al.) | Supplementary arm justification | [ ] |
| Platt scaling / isotonic calibration | Stage 6 method | [ ] |
| Brier score / expected calibration error | Stage 6 metrics | [ ] |
| PR-AUC preferred over ROC-AUC under imbalance | Metric choice defence | [ ] |
| Comprehensiveness/sufficiency (see #16) | O4 fidelity metrics | [ ] |
| Data leakage from duplicates in ML evaluation | Stage 3 defence | [ ] |

---

# Verification log

| Date | Item | Outcome |
|---|---|---|
| 2026-08-07 | Ledger created | 16 unverified claims logged; 9 already inside finalised documents |
| 2026-08-07 | Item 17 added | Illustrative worked-example figures flagged as never-citable |
| 2026-08-26 | Part C rebuilt | 13 Ch 1–2 sources logged with ranking + read status; second-hand rule restated; Mohiddin/Ullah/Goud marked not-currently-cited |
| 2026-08-26 | Item 18 added | Software licence claims logged as unverified |
| 2026-08-27 | Data audit run and corrected | Items #4, #7, #9 VERIFIED; #5 measured, corrected (duplicate-count bug), fully VERIFIED; #3 measured, PARTIALLY verified (field coverage closed, evaluable coverage provisional/deferred) |
| 2026-08-27 | `decisions.md` correction identified and applied | "English Teacher Abroad" cluster is legitimate, not fraudulent — corrected as an appended note, not a silent edit |
| 2026-08-27 | Item 19 added and closed | Two unattributed PDF reports + a supervisor-suggested dataset (DIFrauD) checked against primary sources; all four recommended "second datasets" found to be EMSCAD derivatives and rejected |
| 2026-08-27 | Deadline confirmed | ~1 month remaining — several Part B items (esp. #14, Tier 2 API access) now urgent rather than background tasks |
| 2026-09-20 | Item 14 verified and closed | Greenhouse, Lever, USAJOBS, Arbeitnow, Adzuna all confirmed genuinely free and accessible against their own current documentation; Indeed's 2023 retirement reconfirmed. Fraudulent-side sourcing (scam repositories/advisories) still unverified — next to check. |
| 2026-10-07 | Item 20 added and closed | 24 Tier 2 fraud-side postings collected from BBB Scam Tracker via Claude in Chrome, provenance (unique permalink per report) verified against the live page's own DOM. Labelled "fraudulent by report," consistent with the 2026-08-07 provenance-labelling decision. A source-side near-duplicate pattern (the same report filed under 3+ distinct Scam IDs) was found and logged as a Chapter 6 limitation candidate. |
