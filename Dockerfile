# Deployment image for the credibility-scoring API (Stage 8 artefact).
# Builds and serves the EXISTING FastAPI app (src/api/main.py) completely
# unchanged -- no retraining, no code changes, no new feature logic. This file
# only (1) installs a CPU-only torch build (the dev env pins a CUDA wheel that
# free hosting has no GPU for) and (2) downloads, at build time, the 4 model
# files src/api/pipeline.py and src/explain/shap_explain.py actually load for
# seed 0 -- not the full models/ folder (which also holds seeds 1-2 and the
# 5 ablation arms, used only for Stage 9 evaluation, never by the live API).
#
# Model weights are NOT committed to this repo (same .gitignore policy as
# always -- *.joblib / *.pt stay out of git). They are pulled from a separate,
# free, public Hugging Face model repo during `docker build`, so they end up
# baked into the image with zero runtime network dependency and zero added
# cold-start delay when Render wakes the service from sleep.
#
# SETUP REQUIRED BEFORE FIRST DEPLOY:
#   1. Create a free public model repo at https://huggingface.co/new
#   2. Upload these 4 files from your models/ folder to it:
#        distilbert_fused_state_dict_seed0.pt
#        stage6_calibrator.joblib
#        distilbert_structured_feature_meta_seed0.joblib
#        distilbert_structured_scaler_seed0.joblib
#   3. Replace <HF_USERNAME>/<HF_REPO> below with your real repo id.

FROM python:3.13-slim

WORKDIR /app

# tesseract-ocr: required for POST /extract-image (OCR pre-fill route).
# curl: used below to fetch the model weights at build time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY src/ src/
COPY frontend/ frontend/

# --- Model weights (seed0 only) ---
ARG HF_MODEL_REPO=<HF_USERNAME>/<HF_REPO>
RUN mkdir -p models && \
    curl -fL -o models/distilbert_fused_state_dict_seed0.pt \
      "https://huggingface.co/${HF_MODEL_REPO}/resolve/main/distilbert_fused_state_dict_seed0.pt" && \
    curl -fL -o models/stage6_calibrator.joblib \
      "https://huggingface.co/${HF_MODEL_REPO}/resolve/main/stage6_calibrator.joblib" && \
    curl -fL -o models/distilbert_structured_feature_meta_seed0.joblib \
      "https://huggingface.co/${HF_MODEL_REPO}/resolve/main/distilbert_structured_feature_meta_seed0.joblib" && \
    curl -fL -o models/distilbert_structured_scaler_seed0.joblib \
      "https://huggingface.co/${HF_MODEL_REPO}/resolve/main/distilbert_structured_scaler_seed0.joblib"

ENV PORT=8000
EXPOSE 8000

# Shell form (not exec-array form) so $PORT -- which Render sets at runtime --
# actually gets substituted; Render requires the app to bind to that port.
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
