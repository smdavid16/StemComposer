FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# 1. Install System Dependencies + Build Essentials
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    # --- ADDED THESE FOR SOX ---
    libsox-dev \
    gcc \
    g++ \
    make \
    # ---------------------------
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Upgrade pip first (helps with modern wheels)
RUN pip install --upgrade pip

# 3. Install Python Dependencies
# We split nussl and demucs to make debugging easier if one fails
RUN pip install --no-cache-dir \
    demucs \
    librosa \
    celery \
    redis \
    soundfile

# Nussl often triggers the soxbindings build, so we run it here
RUN pip install --no-cache-dir nussl

# ... (rest of your Dockerfile)
