"""
Stage 4 — Multi-signal evidence extraction (E1-E4)
====================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    Convert the Stage-1-loaded posting fields into the four tagged evidence categories
    defined in the taxonomy (methodology.md, "Evidence taxonomy (O1)"):
      E1  Text / content cues           -- suspicious-phrase lexicon matches
                                            (TF-IDF / embeddings are Stage 5's job: they
                                            must be fit on train only, so they are NOT
                                            built here.)
      E2  Identity & contact cues       -- company_profile presence/length, location
                                            specificity, contact-token counts (Stage 1)
      E3  Metadata completeness         -- 9 structured-field presence flags + composite
      E4  Text-metadata consistency     -- real C1-C6 lexicons, replacing every
                                            provisional pattern from the August audit

INPUT
    A DataFrame already produced by `src.ingestion.load_emscad.load_emscad()` -- this
    module assumes Stage 1's contact-token columns and `{field}_missing` flags already
    exist, and does not repeat that work.

EVERY FEATURE IS TAGGED (E1_/E2_/E3_/C1_.../C6_ column prefixes) so Stage 9's
leave-one-category-out ablation can drop a whole category cleanly. Where a single raw
field feeds two categories (location -> E2 and C2/E4; salary_range -> E3 and C6/E4), both
tagged columns are produced from it and the overlap is documented here, not hidden --
methodology.md's "Ablation protocol" section already commits to reporting it.

WHY THE REAL C1-C6 LEXICONS AREN'T TUNED AGAINST THE 200-POSTING AUDIT SAMPLE
    The Stage 2 manual audit (`reports/stage2_disagreements_for_review.txt`) is the only
    human-labelled signal this project has about whether a consistency rule's design is
    reasonable. If these lexicons were adjusted row-by-row until they agreed with those
    200 judgements, any later claim that the rules "agree with human judgement" would be
    circular -- the same failure mode the project's own guardrail names directly: "a
    threshold set after seeing results is not a threshold." Instead, each rule below is
    redesigned on the general PRINCIPLE the disagreement notes revealed -- overwhelmingly,
    that the provisional patterns conflated "text merely mentions this topic" with
    "evaluable" (both operands present), and conflated "evaluable" with "contradicts".
    This module fixes that conflation structurally (separate evaluable vs. contradiction
    columns, evidence messages) rather than hand-fitting to the 200 known answers. The
    200-sample notes also surfaced two inconsistency patterns outside the fixed C1-C6
    taxonomy -- title-vs-body role mismatches and company_profile-vs-description employer
    mismatches -- these are deliberately NOT coded as a new rule (decisions.md fixes the
    taxonomy at six rules); they are logged as a future-work finding instead.

C6 RECONCILIATION WITH DECISION 0.3
    Decision 0.3 (2026-10-06, itself flagged as a reconstruction, not recovered original
    reasoning) proposed redefining C6 as "text names a dollar figure while salary_range is
    ABSENT" specifically to avoid a label-conditioned numeric threshold. But every other
    part of this project's C6 infrastructure -- the Stage 2 worksheet, the already-reported
    O1 field-coverage figure (26.5%, methodology.md, 2026-10-08) -- is built on the
    opposite gate: field_present == Y. Flipping C6's trigger condition now would silently
    invalidate an already-published result. This module keeps the field_present == Y gate
    (consistent with C1,C3-C5 and with what's already reported), and satisfies Decision
    0.3's actual underlying concern -- no label-conditioned threshold -- two ways: (1)
    C6_contradiction uses a deliberately loose, non-label-tuned order-of-magnitude sanity
    margin (a parsed text figure under half the range's low end or over 3x its high end),
    not a tuned percentage; (2) Decision 0.3's original idea (text names a figure while the
    field is absent) is kept too, as a separate, clearly-labelled supplementary column
    (`C6_text_salary_field_absent`) that does not feed the main C6_evaluable/contradiction
    pair or the already-reported coverage figure. See decisions.md, 2026-10-08.

GAZETTEERS (C2, "first real attempt" per PROJECT_PLAN.md -- not claimed exhaustive)
    ISO-3166 country names and US state names/abbreviations are stable, standard reference
    data (not a measured or asserted research claim) and are hardcoded rather than adding a
    new pip dependency the student's real venv would also need. The city list is a
    deliberately modest set of major, unambiguous world cities -- large enough to catch
    common cases, openly incomplete. A location mention this module cannot recognise is
    reported as "not evaluable", never silently treated as "no contradiction".

THIS MODULE DOES NOT
    - Fit any vectoriser, scaler, or encoder (Stage 5's job, fit on train rows only).
    - Decide model-level missing-value imputation (Stage 1's "never impute" guardrail
      applies to these features too -- an evaluable=N / NA row is a real, reported state,
      not filled in).
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================================
# E1 -- Text / content cues: suspicious-phrase lexicon
# ============================================================================
# Grouped by the kind of red flag, each group reported separately (for explanation
# messages) as well as pooled into one E1_suspicious_phrase_count. Phrases are drawn from
# widely-documented employment-scam indicators (e.g. FTC/IC3 job-scam advisories) and from
# patterns repeatedly named in the Stage 2 audit's own free-text notes (e.g. "scam
# template", "pay-to-join structure", "advance-fee style", "guaranteed income",
# "commission-based income claim") -- used here only as qualitative inspiration for which
# KINDS of phrase to look for, never tuned to make any specific one of the 200 postings
# match or not match.
E1_LEXICON = {
    "advance_fee": [
        r"\bprocessing fee\b", r"\bregistration fee\b", r"\btraining fee\b",
        r"\bstarter kit\b", r"\bpay(?:ment)? to start\b", r"\$\s*\d+\s*to start\b",
        r"\bstarting cost\b", r"\bbuy(?:ing)? (?:your own )?equipment\b",
        r"\bsend (?:us )?(?:a )?(?:deposit|fee)\b",
    ],
    "unrealistic_earnings": [
        r"\bguaranteed (?:income|pay|earnings)\b", r"\bsix figures?\b",
        r"\bunlimited earning\b", r"\bearn \$\d", r"\bmake \$\d+[,\d]*\s*(?:a|per)\s*(?:day|week)\b",
        r"\bno experience necessary\b", r"\bno experience required\b",
        r"\bwork (?:just |only )?\d+\s*(?:minutes|hours)\s*a\s*day\b",
    ],
    "off_platform_contact": [
        r"\bcontact (?:me|us) (?:directly )?(?:at|via) (?:my |our )?(?:personal )?(?:email|whatsapp|telegram|skype)\b",
        r"\btext (?:me|us) (?:at|on)\b", r"\breach out (?:to me )?(?:on|via) whatsapp\b",
    ],
    "urgency_pressure": [
        r"\bact now\b", r"\bimmediate(?:ly)? (?:hiring|start)\b", r"\burgent(?:ly)? (?:hiring|needed)\b",
        r"\blimited (?:spots|positions|time)\b", r"\bhire on the spot\b",
    ],
    "personal_info_request": [
        r"\bsocial security number\b", r"\bssn\b", r"\bbank (?:account|routing) (?:number|details)\b",
        r"\bcopy of your (?:passport|id|driver'?s license)\b", r"\bdate of birth\b.{0,40}\brequired\b",
    ],
    "vague_employer": [
        r"\ba (?:leading|growing|reputable) company\b(?!.{0,80}\bnamed\b)",
        r"\bundisclosed (?:company|employer)\b", r"\bconfidential (?:company|client)\b",
    ],
}
_E1_COMPILED = {
    group: [re.compile(p, re.IGNORECASE) for p in patterns]
    for group, patterns in E1_LEXICON.items()
}

E1_TEXT_COLS = ["title", "description", "requirements", "benefits"]


def extract_e1(df: pd.DataFrame) -> pd.DataFrame:
    """E1 -- suspicious-phrase lexicon matches, grouped and pooled."""
    out = pd.DataFrame(index=df.index)
    blob = df[[c for c in E1_TEXT_COLS if c in df.columns]].fillna("").agg(" ".join, axis=1)

    total = pd.Series(0, index=df.index)
    matched_groups = pd.Series([[] for _ in range(len(df))], index=df.index)
    for group, patterns in _E1_COMPILED.items():
        hit = pd.Series(False, index=df.index)
        for pat in patterns:
            hit = hit | blob.str.contains(pat)
        out[f"E1_phrase_{group}"] = hit.astype(int)
        total = total + hit.astype(int)
        for idx in df.index[hit]:
            matched_groups.at[idx] = matched_groups.at[idx] + [group]

    out["E1_suspicious_phrase_count"] = total
    out["E1_suspicious_phrase_groups"] = matched_groups.map(lambda g: ",".join(g))
    return out


# ============================================================================
# E2 -- Identity & contact cues
# ============================================================================


def _location_specificity(loc: str) -> str:
    """'COUNTRY, REGION, CITY' -> 'none' / 'country_only' / 'region' / 'city'."""
    if loc is None or (isinstance(loc, float) and pd.isna(loc)):
        return "none"
    parts = [p.strip() for p in str(loc).split(",")]
    while len(parts) < 3:
        parts.append("")
    country, region, city = parts[0], parts[1], parts[2]
    if city:
        return "city"
    if region:
        return "region"
    if country:
        return "country_only"
    return "none"


def extract_e2(df: pd.DataFrame) -> pd.DataFrame:
    """E2 -- company_profile presence/length, location specificity, contact tokens.

    Contact-token counts are Stage 1's output (url/email/phone_token_count), already
    computed before HTML stripping per Guardrail 7 -- just tagged E2_ here, not
    recomputed, to avoid the two implementations silently drifting apart.
    """
    out = pd.DataFrame(index=df.index)

    profile = df["company_profile"].fillna("")
    out["E2_company_profile_present"] = (profile.str.strip() != "").astype(int)
    out["E2_company_profile_length"] = profile.str.len()

    out["E2_location_specificity"] = df["location"].map(_location_specificity)

    for src_col, tag in [
        ("url_token_count", "E2_url_token_count"),
        ("email_token_count", "E2_email_token_count"),
        ("phone_token_count", "E2_phone_token_count"),
    ]:
        if src_col in df.columns:
            out[tag] = df[src_col]
        else:
            raise KeyError(
                f"'{src_col}' missing -- run src.ingestion.load_emscad.load_emscad() "
                f"first (Stage 1 must run before Stage 4)."
            )

    return out


# ============================================================================
# E3 -- Metadata completeness
# ============================================================================
# Same 9 fields Stage 1 already flags missingness for (STRUCT_COLS in load_emscad.py).
E3_FIELDS = [
    "department", "salary_range", "employment_type", "required_experience",
    "required_education", "industry", "function", "has_company_logo", "has_questions",
]


def extract_e3(df: pd.DataFrame) -> pd.DataFrame:
    """E3 -- 9 presence flags (inverse of Stage 1's `_missing` flags) + composite score.

    Composite = simple equal-weighted proportion of the 9 fields present (mean of the 9
    binary flags). No field is weighted more than another -- Research_Methodology_Final.docx
    says "weighted proportion" without naming specific weights, and no other project
    document assigns unequal weights, so equal weighting is the documented default here.
    Revisit if a supervisor-agreed weighting scheme is set later (log in decisions.md).
    """
    out = pd.DataFrame(index=df.index)
    present_cols = []
    for field in E3_FIELDS:
        missing_col = f"{field}_missing"
        if missing_col not in df.columns:
            raise KeyError(
                f"'{missing_col}' missing -- run src.ingestion.load_emscad.load_emscad() "
                f"first (Stage 1 must run before Stage 4)."
            )
        present_col = f"E3_{field}_present"
        out[present_col] = (~df[missing_col].astype(bool)).astype(int)
        present_cols.append(present_col)

    out["E3_completeness_score"] = out[present_cols].mean(axis=1)
    return out


# ============================================================================
# E4 -- Text-metadata consistency: real C1-C6 lexicons
# ============================================================================
# Every rule below produces exactly three columns:
#   {rule}_evaluable      Y/N  -- both operands (field + an unambiguous text signal) present
#   {rule}_contradiction  Y/N/NA -- NA when not evaluable
#   {rule}_evidence       str  -- short human-readable reason (Stage 7 rule-message input)
# This separates "could we even check" from "did it actually conflict" -- the provisional
# August patterns conflated the two, which is what the Stage 2 disagreement notes mostly
# surfaced (pattern flag=Y on postings the human coder correctly judged non-contradictory).

_WS = re.compile(r"\s+")


def _norm_text(s) -> str:
    s = str(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"#[A-Z_]+_[0-9a-fA-F]+#", " ", s)
    s = s.lower()
    s = _WS.sub(" ", s).strip()
    return s


# --- C1: telecommuting vs. remote/on-site language -------------------------
# "work from home"/"work from anywhere" are ambiguous on their own: in the corpus they
# overwhelmingly appear as a flexible-working PERK ("ability to occasionally work from
# home", "work from home Wednesdays", "flexible working hours, ability to work from
# home") rather than an assertion that the position itself is remote. A first full-corpus
# run (2026-10-08) found 197/223 C1 "contradictions" (88%) traced to the bare phrase
# "work from home" alone, and manual inspection of a random sample of those showed most
# were perk mentions, not position claims -- a precision bug, not a real signal. Fixed by
# requiring a position-asserting cue near the phrase and excluding a nearby perk/
# conditional cue, rather than matching the bare phrase. This is a general-principle fix
# (perk-framing vs. position-framing is a real linguistic distinction, checked against
# the actual matched text) -- not a fit to the Stage 2 audit sample (see module docstring).
C1_REMOTE_UNAMBIGUOUS = re.compile(
    r"\b(?:100% remote|fully remote|entirely remote|remote[- ]only|"
    r"telecommute from home|remote position|remote role|virtual position)\b"
)
_WFH_MENTION_RE = re.compile(r"work from home|work from anywhere")
_WFH_POSITION_CUE_RE = re.compile(
    r"\b(?:position|job|role|opportunity|vacancy|this is a|full[- ]time|100%|fully|entirely)\b"
)
_WFH_PERK_CUE_RE = re.compile(
    r"\b(?:ability to|able to|occasionally|flexible|sometimes|if required|if needed|"
    r"when needed|option(?:al)? to|can work|you can|allowed to|choose to|benefit|perk|"
    r"days?|wednesdays?|mondays?|tuesdays?|thursdays?|fridays?)\b"
)
_WFH_WINDOW_BEFORE = 40
_WFH_WINDOW_AFTER = 25

# A second precision bug found in the same full-corpus run: literal-phrase matching
# ignores negation, so "this is NOT a remote position" still matched "remote position"
# and was flagged as a contradiction even though the text and the field agree
# (telecommuting == 0). Any of C1's phrase matches can be negated this way, so negation
# is checked generically rather than patched into one phrase at a time.
_NEGATION_CUE_RE = re.compile(r"\b(?:not|n't|never|without|no longer)\b")
_NEGATION_WINDOW = 20


def _preceded_by_negation(text_norm: str, pos: int) -> bool:
    window = text_norm[max(0, pos - _NEGATION_WINDOW):pos]
    return bool(_NEGATION_CUE_RE.search(window))


def _any_unnegated_match(pattern: "re.Pattern", text_norm: str) -> bool:
    return any(
        not _preceded_by_negation(text_norm, m.start())
        for m in pattern.finditer(text_norm)
    )


def _wfh_is_position_claim(text_norm: str) -> bool:
    """True if a 'work from home'/'work from anywhere' mention looks like it is
    describing the position itself rather than a flexible-working perk, and isn't
    negated (e.g. "not a work from home position")."""
    for m in _WFH_MENTION_RE.finditer(text_norm):
        if _preceded_by_negation(text_norm, m.start()):
            continue
        start = max(0, m.start() - _WFH_WINDOW_BEFORE)
        end = min(len(text_norm), m.end() + _WFH_WINDOW_AFTER)
        window = text_norm[start:end]
        if _WFH_PERK_CUE_RE.search(window):
            continue
        if _WFH_POSITION_CUE_RE.search(window):
            return True
    return False


C1_ONSITE_STRONG = re.compile(
    r"\b(?:on[- ]site only|in[- ]office required|no remote option|"
    r"must (?:be able to )?commute|must relocate|relocation required|"
    r"must (?:be )?(?:based|located) in our office|report to our office|"
    r"must be located in|must work from our office)\b"
)


def _c1_row(telecommuting, text_norm):
    remote = _any_unnegated_match(C1_REMOTE_UNAMBIGUOUS, text_norm) or _wfh_is_position_claim(text_norm)
    onsite = _any_unnegated_match(C1_ONSITE_STRONG, text_norm)
    if remote and onsite:
        return "N", "NA", "both remote- and onsite-only language present; ambiguous"
    if not remote and not onsite:
        return "N", "NA", "no unambiguous arrangement language in text"
    if remote:
        contra = "Y" if telecommuting == 0 else "N"
        return "Y", contra, "text asserts fully remote"
    contra = "Y" if telecommuting == 1 else "N"
    return "Y", contra, "text requires on-site presence"


# --- C2: location field vs. place named in text (first real attempt) -------
_ISO_COUNTRIES = {
    "US": "united states", "GB": "united kingdom", "CA": "canada", "AU": "australia",
    "DE": "germany", "FR": "france", "NL": "netherlands", "IE": "ireland", "ES": "spain",
    "IT": "italy", "GR": "greece", "PL": "poland", "SE": "sweden", "NO": "norway",
    "DK": "denmark", "FI": "finland", "CH": "switzerland", "AT": "austria",
    "BE": "belgium", "PT": "portugal", "NZ": "new zealand", "IN": "india",
    "PH": "philippines", "SG": "singapore", "HK": "hong kong", "JP": "japan",
    "CN": "china", "ZA": "south africa", "BR": "brazil", "MX": "mexico",
    "AE": "united arab emirates", "IL": "israel", "RU": "russia", "UA": "ukraine",
    "RO": "romania", "CZ": "czech republic", "TR": "turkey", "EG": "egypt",
    "PK": "pakistan", "BD": "bangladesh", "MY": "malaysia", "ID": "indonesia",
    "TH": "thailand", "VN": "vietnam", "KR": "south korea", "AR": "argentina",
    "CL": "chile", "CO": "colombia", "NG": "nigeria", "KE": "kenya", "SA": "saudi arabia",
    "QA": "qatar", "LU": "luxembourg", "IS": "iceland", "HU": "hungary", "BG": "bulgaria",
}
_US_STATES = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas", "CA": "california",
    "CO": "colorado", "CT": "connecticut", "DE": "delaware", "FL": "florida", "GA": "georgia",
    "HI": "hawaii", "ID": "idaho", "IL": "illinois", "IN": "indiana", "IA": "iowa",
    "KS": "kansas", "KY": "kentucky", "LA": "louisiana", "ME": "maine", "MD": "maryland",
    "MA": "massachusetts", "MI": "michigan", "MN": "minnesota", "MS": "mississippi",
    "MO": "missouri", "MT": "montana", "NE": "nebraska", "NV": "nevada", "NH": "new hampshire",
    "NJ": "new jersey", "NM": "new mexico", "NY": "new york", "NC": "north carolina",
    "ND": "north dakota", "OH": "ohio", "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania",
    "RI": "rhode island", "SC": "south carolina", "SD": "south dakota", "TN": "tennessee",
    "TX": "texas", "UT": "utah", "VT": "vermont", "VA": "virginia", "WA": "washington",
    "WV": "west virginia", "WI": "wisconsin", "WY": "wyoming", "DC": "washington dc",
}
# Deliberately modest, unambiguous major-city list -- not exhaustive (documented above).
_MAJOR_CITIES = {
    "new york": "US", "san francisco": "US", "los angeles": "US", "chicago": "US",
    "boston": "US", "seattle": "US", "austin": "US", "denver": "US", "atlanta": "US",
    "houston": "US", "dallas": "US", "miami": "US", "philadelphia": "US",
    "london": "GB", "manchester": "GB", "birmingham": "GB", "edinburgh": "GB",
    "toronto": "CA", "vancouver": "CA", "montreal": "CA", "ottawa": "CA",
    "sydney": "AU", "melbourne": "AU", "brisbane": "AU", "perth": "AU",
    "berlin": "DE", "munich": "DE", "hamburg": "DE", "frankfurt": "DE",
    "paris": "FR", "amsterdam": "NL", "dublin": "IE", "madrid": "ES", "barcelona": "ES",
    "rome": "IT", "milan": "IT", "athens": "GR", "warsaw": "PL", "stockholm": "SE",
    "oslo": "NO", "copenhagen": "DK", "helsinki": "FI", "zurich": "CH", "vienna": "AT",
    "brussels": "BE", "lisbon": "PT", "wellington": "NZ", "auckland": "NZ",
    "mumbai": "IN", "bangalore": "IN", "delhi": "IN", "manila": "PH", "cebu": "PH",
    "singapore": "SG", "hong kong": "HK", "tokyo": "JP", "beijing": "CN", "shanghai": "CN",
    "cape town": "ZA", "johannesburg": "ZA", "sao paulo": "BR", "mexico city": "MX",
    "dubai": "AE", "tel aviv": "IL", "moscow": "RU", "istanbul": "TR", "cairo": "EG",
}
_PLACE_CUE = re.compile(
    r"\b(?:based in|location[: ]|relocat\w* to|office in|headquartered in|"
    r"must (?:be |reside )?(?:in|near)|position (?:is )?located in)\s+"
    r"([a-z][a-z .'-]{2,40})"
)


def _c2_row(loc_field: str, text_norm: str):
    specificity = _location_specificity(loc_field)
    if specificity == "none":
        return "N", "NA", "structured location field is blank"

    parts = [p.strip().lower() for p in str(loc_field).split(",")]
    while len(parts) < 3:
        parts.append("")
    field_country, field_region, field_city = parts[0], parts[1], parts[2]

    # Candidates come ONLY from an explicit location cue phrase ("based in X",
    # "location: X", "must relocate to X", ...) -- NOT a blind scan of the whole text.
    # A blind scan false-positives constantly: a company_profile routinely names other
    # countries in passing ("Canada/US passport holders only", "offices in the UK and
    # India") without that being a claim about where THIS job is. Requiring a cue phrase
    # catches S'049-style genuine mismatches the Stage 2 notes flagged (a location named
    # as the job's own) while skipping incidental country mentions.
    candidates = [m.group(1).strip() for m in _PLACE_CUE.finditer(text_norm)]
    if not candidates:
        return "N", "NA", "no location cue phrase ('based in', 'relocate to', ...) found in text"

    found_city_country = None
    found_country_name = None
    for cand in candidates:
        for city, country in _MAJOR_CITIES.items():
            if city in cand:
                found_city_country = (city, country)
                break
        if found_city_country:
            break
    if found_city_country is None:
        for cand in candidates:
            for name in _ISO_COUNTRIES.values():
                if name in cand:
                    found_country_name = name
                    break
            if found_country_name:
                break

    if found_city_country is None and found_country_name is None:
        return "N", "NA", "cue phrase present but place name not in lexicon (partial gazetteer)"

    if found_city_country is not None:
        city, country_code = found_city_country
        field_country_name = _ISO_COUNTRIES.get(field_country.upper(), field_country)
        text_country_name = _ISO_COUNTRIES.get(country_code, country_code)
        if field_country and text_country_name != field_country_name:
            return "Y", "Y", f"text names '{city}' ({text_country_name}), field says {field_country_name}"
        return "Y", "N", f"text names '{city}', consistent with field country"

    field_country_name = _ISO_COUNTRIES.get(field_country.upper(), field_country)
    if field_country and found_country_name != field_country_name:
        return "Y", "Y", f"text names country '{found_country_name}', field says '{field_country_name}'"
    return "Y", "N", f"text country mention consistent with field"


# --- C3: employment_type vs. arrangement language ---------------------------
# Another precision bug found in the same full-corpus run (2026-10-08): bare
# "short-term"/"fixed-term" fired on completely unrelated text -- most commonly
# "short-term disability" / "long-term disability", standard US benefits-plan
# boilerplate that has nothing to do with the advertised role's employment type (95 of
# 252 "Temporary"-signal contradictions traced to exactly this phrase). Bare "seasonal"
# had the same problem in a different shape: it can describe OTHER staff mentioned in
# the posting ("...all employees (80 full-time plus 200 seasonal workers)...") rather
# than the advertised role. Fixed by dropping the polysemous bare phrases entirely and
# requiring "seasonal" to be followed by a role-noun that ties it to the advertised
# position, consistent with the general-principle approach used for C1/C6 above.
_C3_SIGNALS = {
    "Full-time": re.compile(r"\b(?:full[- ]time|40 hours (?:a|per) week)\b"),
    "Part-time": re.compile(r"\bpart[- ]time\b"),
    "Contract": re.compile(r"\b(?:independent contractor|1099|contract(?:or)? position)\b"),
    "Temporary": re.compile(
        r"\b(?:temporary position|seasonal (?:position|role|job|work|employment|basis|hire|staff))\b"
    ),
}


def _c3_row(employment_type: str, text_norm: str):
    if not employment_type or employment_type == "Other":
        return "N", "NA", "field blank or 'Other' (too ambiguous to compare)"
    hits = {k: bool(v.search(text_norm)) for k, v in _C3_SIGNALS.items()}
    present = [k for k, v in hits.items() if v]
    if len(present) != 1:
        return "N", "NA", "no single unambiguous arrangement signal in text"
    signal = present[0]
    if signal == employment_type:
        return "Y", "N", f"text signal '{signal}' matches field"
    return "Y", "Y", f"text signal '{signal}' conflicts with field '{employment_type}'"


# --- C4: required_experience vs. "N years" in text --------------------------
# A bare "\d+ years?" match is far too loose: it fires on "been in business for 20
# years", "must be at least 25 years or older", "16-18 year olds" (age restrictions),
# none of which are an experience requirement. Sanity-checked against a 300-row sample
# before this fix -- those were the three dominant false-positive shapes found. Two
# guards: (1) exclude age phrasing outright, (2) require "experience"/"exp" within a
# nearby window, not just anywhere in the whole posting.
_YEARS_RE = re.compile(r"\b(\d{1,2})\s*\+?\s*(?:or more\s*)?years?\b")
_AGE_PHRASE_RE = re.compile(r"years?\s*(?:old|of age|or older|or younger)")
_EXPERIENCE_CONTEXT_RE = re.compile(r"\bexperience\b|\bexp\.?\b")
_YEARS_WINDOW_BEFORE = 15
_YEARS_WINDOW_AFTER = 40

_EXP_ORDER = {
    "Internship": 0, "Entry level": 1, "Associate": 2,
    "Mid-Senior level": 3, "Director": 4, "Executive": 5,
}


def _years_to_tier(n: int) -> int:
    if n <= 1:
        return 0
    if n <= 3:
        return 1
    if n <= 6:
        return 2
    if n <= 10:
        return 3
    return 4


def _years_of_experience_mentions(text_norm: str):
    """Years figures that are plausibly an EXPERIENCE requirement, not an age
    restriction or unrelated "N years in business" mention. See the module note above
    _YEARS_RE for why this guard exists."""
    years = []
    for m in _YEARS_RE.finditer(text_norm):
        if _AGE_PHRASE_RE.search(text_norm[m.start(): m.end() + 20]):
            continue
        window = text_norm[max(0, m.start() - _YEARS_WINDOW_BEFORE): m.end() + _YEARS_WINDOW_AFTER]
        if _EXPERIENCE_CONTEXT_RE.search(window):
            years.append(int(m.group(1)))
    return years


def _c4_row(required_experience: str, text_norm: str):
    if not required_experience or required_experience == "Not Applicable":
        return "N", "NA", "field blank or 'Not Applicable'"
    matches = _years_of_experience_mentions(text_norm)
    if not matches:
        return "N", "NA", "no 'N years (of) experience' figure found in text"
    text_years = max(matches)
    text_tier = _years_to_tier(text_years)
    field_tier = _EXP_ORDER.get(required_experience)
    if field_tier is None:
        return "N", "NA", f"unrecognised field value '{required_experience}'"
    gap = abs(text_tier - field_tier)
    if gap >= 3:
        return "Y", "Y", f"text implies ~{text_years}y, field says '{required_experience}' (large gap)"
    return "Y", "N", f"text implies ~{text_years}y, roughly consistent with '{required_experience}'"


# --- C5: required_education vs. qualification language ----------------------
_EDU_SIGNALS = [
    (0, re.compile(r"\bno degree (?:required|necessary)\b")),
    (1, re.compile(r"\b(?:high school diploma|ged|high school or equivalent)\b")),
    (2, re.compile(r"\bassociate(?:'s)? degree\b")),
    (3, re.compile(r"\bbachelor'?s?(?: degree)?\b")),
    (4, re.compile(r"\bmaster'?s?(?: degree)?|\bmba\b")),
    (5, re.compile(r"\bphd\b|\bdoctorate\b")),
]
_EDU_FIELD_TIER = {
    "Some High School Coursework": 0, "High School or equivalent": 1,
    "Vocational - HS Diploma": 1, "Vocational": 1, "Vocational - Degree": 2,
    "Some College Coursework Completed": 2, "Associate Degree": 2, "Certification": 2,
    "Bachelor's Degree": 3, "Master's Degree": 4, "Professional": 4, "Doctorate": 5,
}


def _c5_row(required_education: str, text_norm: str):
    if not required_education or required_education == "Unspecified":
        return "N", "NA", "field blank or 'Unspecified'"
    field_tier = _EDU_FIELD_TIER.get(required_education)
    if field_tier is None:
        return "N", "NA", f"unrecognised field value '{required_education}'"
    text_tiers = [tier for tier, pat in _EDU_SIGNALS if pat.search(text_norm)]
    if not text_tiers:
        return "N", "NA", "no recognisable qualification language in text"
    text_tier = max(text_tiers)
    gap = abs(text_tier - field_tier)
    if gap >= 2:
        return "Y", "Y", f"text qualification tier {text_tier} vs. field '{required_education}' (tier {field_tier})"
    return "Y", "N", f"text qualification roughly consistent with '{required_education}'"


# --- C6: salary_range vs. money figures (see module docstring for the
#         Decision 0.3 reconciliation) -----------------------------------
# Two more precision bugs found in the same full-corpus run (2026-10-08), both in the
# same direction as the C1 fixes above -- the lexicon was too literal about *what* text
# counts as a salary claim:
#   1. "k" (thousands shorthand) was never resolved: "$95k - $105k" parsed as the literal
#      numbers 95 and 105, so a figure that exactly matched the field range ($95,000-
#      $105,000) was reported as "far outside" it.
#   2. `_SALARY_WORD_RE` (a proximity gate meant to require a $ figure to sit near
#      explicit salary/pay language) was defined but never actually used anywhere in the
#      matching logic below -- every dollar figure in the posting (travel reimbursement,
#      sign-on bonus, a product/service cost mentioned in the ad copy) was compared
#      against salary_range, regardless of what it was actually about. This is wired in
#      now rather than left dead.
# Both are general-principle fixes verified against the actual matched text (a "$1,000
# travel/hotel cost for interview" row, a "$156k" row), not a fit to the Stage 2 audit
# sample (see module docstring).
_MONEY_RE = re.compile(r"\$\s*([\d,]{1,9})\s*(k)?\b", re.IGNORECASE)
_SALARY_WORD_RE = re.compile(
    r"\b(?:salary|compensation|pay(?:s)?|wage|earn(?:ings)?|per annum|annually|"
    r"per year|per month|per hour|hourly)\b"
)
_SALARY_CONTEXT_WINDOW_BEFORE = 50
_SALARY_CONTEXT_WINDOW_AFTER = 20
# Floor for a figure with no "k" suffix, to exclude incidental small dollar amounts
# ($5 lunch allowance, etc.) that would otherwise pass the salary-context gate.
_MIN_RAW_DOLLAR_FIGURE = 100


def _parse_money(s: str):
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _salary_context_dollar_figures(text_norm: str):
    """Dollar figures found near explicit salary/pay language, with a trailing 'k'
    (thousands) resolved. Filters out incidental dollar amounts that are not actually
    competing salary claims (see the C6 note above)."""
    figures = []
    for m in _MONEY_RE.finditer(text_norm):
        start = max(0, m.start() - _SALARY_CONTEXT_WINDOW_BEFORE)
        end = min(len(text_norm), m.end() + _SALARY_CONTEXT_WINDOW_AFTER)
        if not _SALARY_WORD_RE.search(text_norm[start:end]):
            continue
        v = _parse_money(m.group(1))
        if v is None:
            continue
        if m.group(2):
            v *= 1000.0
        elif v < _MIN_RAW_DOLLAR_FIGURE:
            continue
        figures.append(v)
    return figures


def _c6_row(salary_range_present: bool, salary_low, salary_high, text_norm: str):
    figures = _salary_context_dollar_figures(text_norm)
    has_dollar_figure = len(figures) > 0

    supplementary = "Y" if (not salary_range_present and has_dollar_figure) else "N"

    if not salary_range_present:
        return "N", "NA", "salary_range absent", supplementary
    if not has_dollar_figure:
        return "N", "NA", "no $ figure near salary/pay language found in text", supplementary

    lo_bound = salary_low * 0.5
    hi_bound = salary_high * 3.0
    outside = [f for f in figures if f < lo_bound or f > hi_bound]
    if outside:
        return (
            "Y", "Y",
            f"text figure ${outside[0]:,.0f} far outside field range ${salary_low:,.0f}-${salary_high:,.0f}",
            supplementary,
        )
    return "Y", "N", f"text figure(s) within a generous margin of field range", supplementary


def extract_e4(df: pd.DataFrame) -> pd.DataFrame:
    """E4 -- real C1-C6 lexicons. Requires Stage 1's `_missing` flags and `salary_range`
    already placeholder-normalised (both done by load_emscad())."""
    n = len(df)
    text_norm = (
        df[["title", "description", "requirements", "benefits"]]
        .fillna("")
        .agg(" ".join, axis=1)
        .map(_norm_text)
    )

    c1_eval, c1_contra, c1_ev = [], [], []
    c2_eval, c2_contra, c2_ev = [], [], []
    c3_eval, c3_contra, c3_ev = [], [], []
    c4_eval, c4_contra, c4_ev = [], [], []
    c5_eval, c5_contra, c5_ev = [], [], []
    c6_eval, c6_contra, c6_ev, c6_supp = [], [], [], []

    salary_present = ~df["salary_range_missing"].astype(bool)
    salary_parsed = df["salary_range"].where(salary_present, None)

    for i, (_, row) in enumerate(df.iterrows()):
        tn = text_norm.iloc[i]

        e, c, ev = _c1_row(row["telecommuting"], tn)
        c1_eval.append(e); c1_contra.append(c); c1_ev.append(ev)

        e, c, ev = _c2_row(row.get("location"), tn)
        c2_eval.append(e); c2_contra.append(c); c2_ev.append(ev)

        et = "" if row["employment_type_missing"] else str(row.get("employment_type") or "")
        e, c, ev = _c3_row(et, tn)
        c3_eval.append(e); c3_contra.append(c); c3_ev.append(ev)

        rex = "" if row["required_experience_missing"] else str(row.get("required_experience") or "")
        e, c, ev = _c4_row(rex, tn)
        c4_eval.append(e); c4_contra.append(c); c4_ev.append(ev)

        redu = "" if row["required_education_missing"] else str(row.get("required_education") or "")
        e, c, ev = _c5_row(redu, tn)
        c5_eval.append(e); c5_contra.append(c); c5_ev.append(ev)

        sp = bool(salary_present.iloc[i])
        lo, hi = None, None
        if sp:
            raw = str(row.get("salary_range") or "")
            m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", raw)
            if m:
                lo, hi = float(m.group(1)), float(m.group(2))
            else:
                sp = False
        e, c, ev, supp = _c6_row(sp, lo, hi, tn)
        c6_eval.append(e); c6_contra.append(c); c6_ev.append(ev); c6_supp.append(supp)

    out = pd.DataFrame(index=df.index)
    out["C1_field_present"] = "Y"  # telecommuting is always present (boolean)
    out["C1_evaluable"] = c1_eval
    out["C1_contradiction"] = c1_contra
    out["C1_evidence"] = c1_ev

    out["C2_field_present"] = df["location"].map(lambda v: "N" if _location_specificity(v) == "none" else "Y")
    out["C2_evaluable"] = c2_eval
    out["C2_contradiction"] = c2_contra
    out["C2_evidence"] = c2_ev

    out["C3_field_present"] = (~df["employment_type_missing"].astype(bool)).map({True: "Y", False: "N"})
    out["C3_evaluable"] = c3_eval
    out["C3_contradiction"] = c3_contra
    out["C3_evidence"] = c3_ev

    out["C4_field_present"] = (~df["required_experience_missing"].astype(bool)).map({True: "Y", False: "N"})
    out["C4_evaluable"] = c4_eval
    out["C4_contradiction"] = c4_contra
    out["C4_evidence"] = c4_ev

    out["C5_field_present"] = (~df["required_education_missing"].astype(bool)).map({True: "Y", False: "N"})
    out["C5_evaluable"] = c5_eval
    out["C5_contradiction"] = c5_contra
    out["C5_evidence"] = c5_ev

    out["C6_field_present"] = salary_present.map({True: "Y", False: "N"})
    out["C6_evaluable"] = c6_eval
    out["C6_contradiction"] = c6_contra
    out["C6_evidence"] = c6_ev
    out["C6_text_salary_field_absent"] = c6_supp  # supplementary, see module docstring

    contra_cols = [f"C{i}_contradiction" for i in (1, 2, 3, 4, 5, 6)]
    out["E4_contradiction_count"] = out[contra_cols].apply(
        lambda r: sum(1 for v in r if v == "Y"), axis=1
    )

    return out


# ============================================================================
# Driver
# ============================================================================


def extract_all(df: pd.DataFrame) -> pd.DataFrame:
    """Run E1-E4 and return the original df with every tagged feature column attached."""
    e1 = extract_e1(df)
    e2 = extract_e2(df)
    e3 = extract_e3(df)
    e4 = extract_e4(df)
    return pd.concat([df, e1, e2, e3, e4], axis=1)


def coverage_report(features: pd.DataFrame) -> dict:
    """Field-presence and evaluable-coverage figures for C1-C6, comparable in shape to
    the August provisional-pattern table in methodology.md (now to be replaced by this)."""
    n = len(features)
    report = {}
    for rule in ("C1", "C2", "C3", "C4", "C5", "C6"):
        present = int((features[f"{rule}_field_present"] == "Y").sum())
        evaluable = int((features[f"{rule}_evaluable"] == "Y").sum())
        contradictions = int((features[f"{rule}_contradiction"] == "Y").sum())
        report[rule] = {
            "field_present": present,
            "field_present_pct": round(100 * present / n, 2),
            "evaluable": evaluable,
            "evaluable_pct": round(100 * evaluable / n, 2),
            "contradictions": contradictions,
            "contradictions_pct_of_evaluable": (
                round(100 * contradictions / evaluable, 2) if evaluable else None
            ),
        }
    at_least_one = int((features["E4_contradiction_count"] > 0).sum())
    any_evaluable = int(
        (
            (features["C1_evaluable"] == "Y") | (features["C2_evaluable"] == "Y") |
            (features["C3_evaluable"] == "Y") | (features["C4_evaluable"] == "Y") |
            (features["C5_evaluable"] == "Y") | (features["C6_evaluable"] == "Y")
        ).sum()
    )
    report["aggregate"] = {
        "n": n,
        "evaluable_by_at_least_one_rule": any_evaluable,
        "evaluable_by_at_least_one_rule_pct": round(100 * any_evaluable / n, 2),
        "mean_rules_evaluable": round(
            sum(
                (features[f"{r}_evaluable"] == "Y").sum() for r in
                ("C1", "C2", "C3", "C4", "C5", "C6")
            ) / n, 3
        ),
        "postings_with_at_least_one_contradiction": at_least_one,
        "postings_with_at_least_one_contradiction_pct": round(100 * at_least_one / n, 2),
    }
    return report


if __name__ == "__main__":
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.ingestion.load_emscad import load_emscad

    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/DataSet.csv"
    df = load_emscad(path)
    features = extract_all(df)
    report = coverage_report(features)

    Path("reports").mkdir(exist_ok=True)
    with open("reports/stage4_coverage_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print("\nWritten: reports/stage4_coverage_report.json")
