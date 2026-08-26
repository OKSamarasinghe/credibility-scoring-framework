# sources.md — Verified Claims & References

_Last updated: 2026-08-26_

> **The rule:** every claim, definition, statistic or method that came from an AI model goes
> here until I have checked it against a **primary** source. Anything still marked
> `Verified: NO` must **not** appear in my dissertation as fact.
>
> **Status key:** ❌ unverified · ⚠️ partially evidenced, needs primary confirmation ·
> ✅ verified against primary source
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

## 3. ❌ Consistency rule field-coverage percentages (C1 100%, C2 98%, C3 81%, C4 61%, C5 55%, C6 16%)

- **Claim:** Per-rule field coverage, printed in the rule table in
  `Research_Methodology_Final.docx` §3.1.
- **From:** AI model, 2026-08-07, **derived by inference** from the Kaggle dataset profile
  I pasted — NOT measured on the actual CSV.
- **Verified:** NO
- **Critical caveat:** These are *field-availability* rates, which are an **upper bound**
  on rule coverage, not rule coverage itself. True triggerable coverage will be lower —
  C2 requires both a parseable `location` **and** a location mention in the description.
- **Action:** **Measure directly in the data audit.** Replace every figure in the .docx
  with the measured value. Until then these numbers are estimates presented as fact, which
  is exactly what this file exists to prevent.

## 4. ⚠️ Boolean fields stored as string literals `'t'` / `'f'`

- **Claim:** In the Kaggle mirror, `telecommuting`, `has_company_logo`, `has_questions`,
  `fraudulent` and `in_balanced_dataset` are strings, not booleans. Stated as fact in
  `Research_Methodology_Final.docx` §2.1.2.
- **From:** AI model inference from the "Mismatched 100%" rows in the profile I pasted.
- **Verified:** PARTIAL — the profile is consistent with this, but the specific `t`/`f`
  encoding is an inference.
- **Action:** Confirm in the audit with `df['fraudulent'].unique()`. If the encoding differs,
  correct §2.1.2. Cheap to check, embarrassing to get wrong.

## 5. ⚠️ Duplicate estimate — ~15,100 unique descriptions, ~11,200 unique titles

- **Claim:** Roughly 2,700 duplicate/near-duplicate postings; used to justify the
  group-aware split.
- **From:** Kaggle dataset profile I pasted (the profiler's own "Unique" counts).
- **Verified:** PARTIAL — the profiler reports *exact* uniqueness on raw strings. My
  methodology claims *near*-duplicates, which requires normalised comparison and will give
  a different (probably larger) number.
- **Action:** Measure exact and normalised duplicate counts separately in the audit.

## 6. ❌ `has_company_logo` may be a dataset artefact rather than a durable fraud signal

- **Claim:** Justifies my targeted ablation in `Research_Methodology_Final.docx` §9.2.
- **From:** AI model, 2026-08-07, from general knowledge. No source given.
- **Verified:** NO
- **Action:** Check whether any published EMSCAD study discusses this. If none does, I must
  reword the methodology to present it as **my own hypothesis motivating the ablation**,
  not as an established concern. Currently it reads as established.

## 7. ⚠️ EMSCAD anonymisation uses hashed placeholder tokens (`#URL_…#`, `#EMAIL_…#`, `#PHONE_…#`)

- **Claim:** Underpins my entire E2 identity/contact feature group.
- **From:** Visible in the sample description in the profile I pasted (`#URL_ec9a1dff…#`).
- **Verified:** PARTIAL — URL tokens directly observed. `#EMAIL_#` and `#PHONE_#` are
  inferred by analogy and **not yet observed**.
- **Action:** Grep the real CSV for each token type and count occurrences. If `#EMAIL_#`
  and `#PHONE_#` do not exist, a large part of E2 collapses and the taxonomy needs revision.
  **This is a high-impact check — do it early.**

## 8. ❌ Full reference — Venable, Pries-Heje & Baskerville, FEDS framework

- **Claim:** Evaluation strategy positioning (ex ante/ex post, artificial/naturalistic) in
  `methodology.md`.
- **From:** Supervisor's field guide + AI model, 2026-08-07.
- **Verified:** NO
- **Action:** Retrieve full reference. Confirm the two axes are named as I have used them.

## 9. ⚠️ EMSCAD composition — 17,880 total; 17,014 legitimate; 866 fraudulent; 2012–2014

- **From:** EMSCAD documentation text I pasted; consistent across multiple papers.
- **Verified:** PARTIAL — well corroborated but not confirmed against my own file.
- **Action:** Confirm by direct count in the audit.

---

# PART B — Claims used in reasoning, not yet in documents

## 10. ❌ FTC: job/employment scam reports nearly tripled since 2020; losses from ~$90m to $500m+ annually

- **From:** AI web search, 2026-08-07. **Secondary reporting** (news/commentary sites), not
  the FTC itself.
- **Verified:** NO
- **Action:** Get figures from the **primary source** — FTC Consumer Sentinel Network Data
  Book. Cite the FTC directly or not at all.
- **Intended use:** Chapter 1 problem motivation; justification for the Tier 2 dataset.

## 11. ❌ BBB: employment scam reports doubled in 2025

- **From:** AI web search, 2026-08-07. Secondary reporting of a BBB study.
- **Verified:** NO
- **Action:** Locate the primary BBB scam study and cite it directly.

## 12. ❌ AI-generated postings have eroded lexical fraud cues (grammar, spelling, generic phrasing)

- **From:** AI web search, 2026-08-07 — commercial/commentary sources, not peer-reviewed.
- **Verified:** NO
- **Importance:** **This is the central motivation for my Tier 2 work and the signal-durability
  hypothesis (E2).** It currently rests on non-academic sources.
- **Action:** Find peer-reviewed support, or an authoritative body (FBI IC3, ITRC). If no
  strong source exists, present it explicitly as **my hypothesis to be tested by experiment
  E2**, not as established fact. That is defensible; asserting it is not.

## 13. ❌ Task-based scams as a distinct contemporary typology

- **From:** AI web search, 2026-08-07 (security-vendor report + BBB commentary).
- **Verified:** NO
- **Action:** Verify against primary reporting before including in the taxonomy extension.

## 14. ❌ Free job-board API availability (Greenhouse, Lever, USAJOBS, Arbeitnow, Adzuna free tier); Indeed Publisher API retired 2023

- **From:** AI web search, 2026-08-07.
- **Verified:** NO
- **Action:** Verify by **actually accessing each endpoint** and reading its current terms
  of service. API availability changes without notice and terms govern whether I may use
  the data at all. Record what I confirm, with the date.

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
- **Risk:** These numbers now sit inside a document the AI reads every session. Months from
  now, while drafting a results chapter, one could be picked up as if it were real.
- **Action:** **Never cite any of them.** Delete this entry only once genuine measured
  values exist and have replaced them.

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
| C6 | Sullivan & Weger (2025). Transparency and Explainability in AI-Assisted Decision Making. SAGE. | 1 | ⚠️ **CONFIRM** | [ ] | ❌ | Ranking not yet verified — do this |
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
| | | |
