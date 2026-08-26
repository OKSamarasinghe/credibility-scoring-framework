# Explainable Credibility Scoring Framework for Online Recruitment Posts

BSc (Hons) Computing final-year individual project — Coventry University / NIBM.
O.K. Samarasinghe — Coventry 16116041, NIBM COBSCCOMP242P-069.

A backend REST API that scores the credibility of online recruitment postings using a
four-category evidence taxonomy (text/content cues, identity & contact cues, metadata
completeness, and text–metadata consistency verification), with calibrated 0–100 output
and human-readable explanations. Built as a Design Science Research artefact.

## Repository structure

- `data/` — dataset documentation (raw data not stored — see data/README.md)
- `audit/` — data audit script and measured results
- `src/` — pipeline: ingestion, feature extraction, models, explainability, API
- `docs/` — project, decisions, methodology and sources logs
- `notebooks/` — exploratory work
- `reports/` — evaluation outputs
- `tests/` — automated tests

## Setup