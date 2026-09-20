# Stage 2 — Manual Audit Coding Instructions

_Defined in advance, 2026-08-27, before any posting is coded. This is the "pre-defined
coding scheme" `methodology.md` requires for O1 validation. Do not revise these rules
partway through the 200 postings — if a genuine ambiguity forces a revision, log it in
`decisions.md`, note which sample_id triggered it, and re-check earlier postings against
the revised rule._

**You are the single coder.** No inter-rater reliability statistic is possible or claimed —
this is a stated limitation, not a flaw to hide.

---

## Before you start

Open `reports/stage2_manual_audit_worksheet.csv` in Excel or Google Sheets. 200 rows, one
posting per row. Columns ending `_MANUAL` are yours to fill. Columns ending
`_REFERENCE_ONLY` are pre-filled by the sampling script using provisional patterns — they
are a hint, not an answer. Trust your own reading of the posting over them.

Work in the `sample_id` order (S001–S200) so progress is trackable. Budget roughly 1–2
minutes per posting for the E1–E4 columns, more for postings where a C-rule needs a close
read of the full text (not just the snippet — open the original CSV row by
`original_csv_index` if the 400-character snippet isn't enough).

---

## Columns E1–E4: is this evidence category observable at all?

For each category, answer **Y**, **N**, or **PARTIAL**.

- **Y** — the category's signal is clearly present and readable in this posting.
- **N** — the category's underlying fields/text are essentially absent (e.g. E3 completeness
  on a posting where nearly every structured field is blank).
- **PARTIAL** — some signal exists but is thin, ambiguous, or only partly usable.

| Category | Ask yourself |
|---|---|
| E1 (text/content) | Is there enough description/requirements text to judge wording, tone, specificity? |
| E2 (identity/contact) | Is there a company_profile, a specific location, or contact-pressure language? |
| E3 (completeness) | Are the structured fields (department, salary, experience, education, etc.) mostly filled or mostly blank? |
| E4 (consistency) | Could you, reading this posting, even attempt to check text against fields — regardless of whether one actually turns out to conflict? |

---

## Columns C1–C6: `{rule}_manual_contradiction_MANUAL`

For **each rule**, first check the `{rule}_field_present` column (pre-filled, mechanical —
trust it, it's a data fact not a judgement). If it's **N**, the rule cannot be evaluated for
this posting — write **NA** and move to the next rule.

If the field is present, read the relevant text yourself and answer:

- **Y** — the text genuinely contradicts the structured field, as a human reader would
  understand "contradiction." Don't be led by the `_REFERENCE_ONLY` pattern flag — it's a
  crude regex and will both over-fire (e.g. matching "commute" in an unrelated sentence)
  and under-fire (missing phrasing outside its fixed vocabulary).
- **N** — the field is present, the text could in principle be checked, and there is no
  contradiction.
- **NA** — the field is present but the text simply doesn't address this dimension at all
  (e.g. `required_education` is filled in, but the description never discusses education in
  any way that could agree or disagree with it).

**Rule-specific reading guidance:**

- **C1** (remote/on-site): does the description describe a working arrangement that
  disagrees with the `telecommuting` flag? Watch for hybrid arrangements — decide now
  whether "2 days remote, 3 in office" counts as a contradiction of a `telecommuting=false`
  flag, and apply that decision consistently for the rest of the 200.
- **C2** (location): field coverage is not pre-filled with a pattern check (C2 evaluable
  coverage is deferred — see `decisions.md`). Read whether the description names a
  location, and whether it disagrees with the structured `location` field.
- **C3** (employment type): does the description describe a working arrangement
  (contract/temporary/freelance/part-time/permanent) that disagrees with `employment_type`?
- **C4** (experience): does the description state a "years of experience" figure that
  disagrees with `required_experience`?
- **C5** (education): does the description's stated qualification requirement disagree with
  `required_education`?
- **C6** (salary): does a compensation figure in the text fall outside the parsed
  `salary_range` bounds?

---

## `notes_MANUAL`

Free text. Use it for: genuine ambiguity you resolved a particular way (so you can defend
the call later), anything that made you want to revise the coding scheme mid-way (don't
revise silently — log it), or any posting that felt like a borderline case worth
highlighting in the O1 write-up.

---

## When you're done

- Save the completed CSV back into `reports/stage2_manual_audit_worksheet.csv` (overwrite
  the template).
- Compute: per-category observability rate (% Y across 200), per-rule agreement rate
  between your `_manual_contradiction` judgement and the `_REFERENCE_ONLY` pattern flag
  (this comparison is a preview of Stage 4, not the final rule-consistency check — the real
  lexicons don't exist yet).
- Log in `methodology.md` under "Taxonomy validation (O1)" and mark at least one signal you
  revised or dropped because the audit contradicted an assumption — an audit that confirms
  everything you already believed wasn't a real check.
