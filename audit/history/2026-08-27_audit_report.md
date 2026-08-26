# EMSCAD Data Audit — measured results

_Run: 2026-08-26 · File: DataSet.csv_

```

==========================================================================
1.  SHAPE AND COLUMNS
==========================================================================
File            : DataSet.csv
Rows            : 17,880
Columns         : 18
Column names    : title, location, department, salary_range, company_profile, description, requirements, benefits, telecommuting, has_company_logo, has_questions, employment_type, required_experience, required_education, industry, function, fraudulent, in_balanced_dataset

Expected 17,880 rows (EMSCAD): MATCH

==========================================================================
2.  BOOLEAN ENCODING  [sources.md #4]
==========================================================================
telecommuting          : ['f', 't']
has_company_logo       : ['f', 't']
has_questions          : ['f', 't']
fraudulent             : ['f', 't']
in_balanced_dataset    : ['f', 't']

RESULT: confirmed — booleans are stored as the string literals 't' and 'f'.
        sources.md #4 can be marked VERIFIED.

==========================================================================
3.  CLASS COMPOSITION  [sources.md #9]
==========================================================================
Fraudulent      : 866   (4.84%)
Legitimate      : 17,014   (95.16%)

Expected 866 fraudulent: MATCH
Expected 17,014 legit  : MATCH

in_balanced_dataset : PRESENT — must be dropped from the feature space (Stage 1).

==========================================================================
4.  FIELD MISSINGNESS  (drives the E3 completeness category)
==========================================================================
Field                      Present   Missing  Missing %
--------------------------------------------------------
title                       17,880         0       0.0%
location                    17,534       346       1.9%
department                   6,327    11,553      64.6%
salary_range                 2,868    15,012      84.0%
company_profile             14,572     3,308      18.5%
description                 17,880         0       0.0%
requirements                15,191     2,689      15.0%
benefits                    10,684     7,196      40.2%
telecommuting               17,880         0       0.0%
has_company_logo            17,880         0       0.0%
has_questions               17,880         0       0.0%
employment_type             14,409     3,471      19.4%
required_experience         10,830     7,050      39.4%
required_education           9,775     8,105      45.3%
industry                    12,977     4,903      27.4%
function                    11,425     6,455      36.1%
fraudulent                  17,880         0       0.0%
in_balanced_dataset         17,880         0       0.0%

==========================================================================
5.  SALARY_RANGE QUALITY
==========================================================================
Present                     : 2,868  (16.0%)
Literal '0-0' placeholder   : 142
Numeric 'lo-hi' parseable   : 2,867
USABLE (parseable, not 0-0) : 2,725  (15.2%)

The usable figure is the real ceiling for consistency rule C6.

==========================================================================
6.  ANONYMISED CONTACT TOKENS  [sources.md #7 — HIGH IMPACT]
==========================================================================
E2 (Identity & Contact Cues) depends on these existing. If #EMAIL_# and
#PHONE_# are absent, a large part of E2 collapses and the taxonomy needs revision.

Token         Postings with >=1  % of rows  Total occurrences
--------------------------------------------------------------
#URL_#                    7,362      41.2%             23,270
#EMAIL_#                  1,377       7.7%              2,368
#PHONE_#                    657       3.7%              1,026

All placeholder token types discovered: ['EMAIL', 'PHONE', 'URL']

RESULT: all three token types present — E2 stands as designed.
        sources.md #7 can be marked VERIFIED.

Token presence by class (is this actually discriminative?):
Token           Fraud %    Legit %    Ratio
--------------------------------------------
#URL_#            42.4%      41.1%     1.03
#EMAIL_#          20.1%       7.1%     2.84
#PHONE_#           9.2%       3.4%     2.72

A ratio well above 1.0 means fraudulent postings carry that token more often.
This is descriptive only — not a modelling result.

==========================================================================
7.  DUPLICATE AND NEAR-DUPLICATE POSTINGS  [sources.md #5]
==========================================================================
Total records                          : 17,880
Unique descriptions (exact, raw)       : 15,095
Unique descriptions (normalised)       : 14,375
Records sitting in a duplicate group    : 4,762  (26.6%)
  (excess-over-unique figure, for reference only: 3,505 — NOT the group-
   membership count; fixed 2026-08-27, see sources.md #5 note)
Duplicate groups (size > 1)            : 1,257
Unique titles                          : 11,231

Normalising finds MORE duplicates than exact matching. The normalised figure
is the one that matters for group-aware partitioning (Stage 3).

Duplicated fraudulent records          : 349 of 866 (40.3%)
Duplicated legitimate records          : 4,412 of 17,014 (25.9%)

If the fraud class is more duplicated, a random split inflates fraud-class
performance specifically — which is exactly the metric this study reports.

Largest fraudulent duplicate clusters:
     22 copies   Home Based Payroll Data Entry Clerk Position - Earn $100-$
     21 copies   Data Entry Admin/Clerical Positions - Work From Home
     21 copies   Cruise Staff Wanted *URGENT*
     21 copies   Home Based Payroll Typist/Data Entry Clerks Positions Avai
     20 copies   Admin Clerk Remote Position

==========================================================================
8.  LOCATION PARSEABILITY  (drives rule C2)
==========================================================================
Location present            : 17,534  (98.1%)
Country component usable    : 17,534  (98.1%)
City component usable       : 15,812  (88.4%)

C2 needs a usable location component AND a location named in the description.

==========================================================================
9.  CONSISTENCY RULE COVERAGE C1-C6  [sources.md #3]
==========================================================================
field coverage    = the structured field the rule reads is present
evaluable coverage = BOTH operands present, so the rule could actually run
Evaluable coverage is the honest number for the methodology table.

Text operand for C3-C6 = description + requirements + benefits (not description alone).

CAVEAT: all evaluable-coverage figures below are provisional — they use this audit
script's own placeholder patterns (REMOTE/PARTTIME/YEARS/EDU/MONEY), not the final
Stage 4 lexicons. Re-measure once those lexicons are frozen. C2 has no evaluable
figure at all yet: its field coverage is an explicit UPPER BOUND, not a measurement —
see the code comment on C2 for why a quick proxy was deliberately not used.

ID   Rule                  Field cov      Evaluable  Was est.   Delta
--------------------------------------------------------------------------
C1   Remote / on-site         100.0%          10.5%      100%  -89.5
C2   Location mismatch         88.4%       DEFERRED       98%     n/a
C3   Employment type           80.6%          12.2%       81%  -68.8
C4   Experience level          60.6%          30.2%       61%  -30.8
C5   Education                 54.7%          27.8%       55%  -27.2
C6   Salary                    15.2%           7.6%       16%   -8.4

For comparison, evaluable coverage using DESCRIPTION ALONE:
   C4: 7.4%   (vs 30.2% using the full body)
   C5: 3.6%   (vs 27.8% using the full body)
   C6: 4.0%   (vs 7.6% using the full body)

ACTION: replace the Field Coverage column in Research_Methodology_Final.docx
        section 3.1 with the EVALUABLE figures above. C1,C3-C6 are provisional
        (placeholder patterns). C2 has no evaluable figure — field coverage only,
        an upper bound. Do NOT mark sources.md #3 fully verified yet.

Postings evaluable by at least one rule : 10,145  (56.7%)
Mean rules evaluable per posting        : 0.88 of 6

==========================================================================
10.  SUMMARY — WHAT TO UPDATE
==========================================================================
sources.md:
  #4 boolean t/f encoding      -> VERIFIED
  #9 class composition         -> VERIFIED
  #7 contact tokens            -> VERIFIED
  #5 duplicate counts          -> VERIFIED (measured figures above; group-membership
                                   count corrected 2026-08-27, was mislabeled)
  #3 rule coverage             -> PARTIALLY VERIFIED. C1,C3-C6 evaluable coverage
                                   measured but PROVISIONAL (placeholder patterns,
                                   not final Stage 4 lexicons). C2 evaluable coverage
                                   NOT measured — field coverage only, reported as
                                   an upper bound. Do not mark #3 fully verified.

Research_Methodology_Final.docx:
  section 3.1  -> replace Field Coverage column with measured evaluable coverage
  section 2.1.2 -> confirm or correct the duplicate and encoding statements

methodology.md:
  'Data audit' results block -> paste from audit_report.md
```
