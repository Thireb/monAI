# =============================================================================
# Dockerfile – build an image that runs this Django project on Arch Linux
# =============================================================================
# Each instruction adds a "layer". Layers are cached, so order matters:
# change code often → put COPY code last; change deps rarely → install deps first.
# =============================================================================

# Base image: Arch Linux (rolling release).
FROM archlinux:latest

# -----------------------------------------------------------------------------
# Venv path: use /opt/venv so a bind mount of . → /app doesn't hide the venv
# -----------------------------------------------------------------------------
ARG VENV_PATH=/opt/venv
ENV VENV_PATH=${VENV_PATH}

# -----------------------------------------------------------------------------
# 1. Install system packages (one RUN = one layer; combine to keep image smaller)
# -----------------------------------------------------------------------------
# - pacman-key: init + populate so package signatures are trusted.
# - Sy archlinux-keyring first: sync DB and install latest keyring so newer
#   package signers (e.g. libseccomp) are trusted before full upgrade.
# - Su: upgrade rest of system; then S: install app + WeasyPrint deps.
# -----------------------------------------------------------------------------
RUN rm -rf /var/cache/pacman/pkg/* 2>/dev/null || true && \
    pacman-key --init && \
    pacman-key --populate archlinux && \
    pacman -Sy archlinux-keyring --noconfirm && \
    pacman -Su --noconfirm && \
    pacman -S --noconfirm \
        base-devel \
        python \
        python-pip \
        cairo \
        pango \
        gdk-pixbuf2 \
    && pacman -Scc --noconfirm

# -----------------------------------------------------------------------------
# 2. Set working directory inside the container
# -----------------------------------------------------------------------------
# All following commands run from /app. When the container runs, the app lives here.
# -----------------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------------
# 3. Copy only requirements first → better cache: code changes don't re-run pip
# -----------------------------------------------------------------------------
COPY requirements.txt .

# -----------------------------------------------------------------------------
# 4. Create virtualenv and install Python dependencies
# -----------------------------------------------------------------------------
# We use Python's built-in venv (no need for the "virtualenv" package).
# -----------------------------------------------------------------------------
RUN python -m venv ${VENV_PATH} && \
    ${VENV_PATH}/bin/pip install --no-cache-dir --upgrade pip && \
    ${VENV_PATH}/bin/pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# 5. Copy the rest of the project into the image
# -----------------------------------------------------------------------------
# .dockerignore excludes venv, .git, __pycache__, etc. config.yaml is copied
# if it exists on your host (needed for Django settings).
# COPY . . also works because it copies into workdirectory which is already set.
# -----------------------------------------------------------------------------
COPY . /app

# -----------------------------------------------------------------------------
# 6. Expose port 8000 (documentation only; mapping is done by run/compose)
# -----------------------------------------------------------------------------
EXPOSE 8000

# -----------------------------------------------------------------------------
# 7. Run migrations then start Django development server on 0.0.0.0:8000
# -----------------------------------------------------------------------------
# Migrate on every start (safe, idempotent) so the DB is ready. Then runserver.
# 0.0.0.0 = listen on all interfaces so you can open http://localhost:8000
# from your host.
# -----------------------------------------------------------------------------
CMD ["/bin/sh", "-c", "${VENV_PATH}/bin/python manage.py migrate --noinput && ${VENV_PATH}/bin/python manage.py runserver 0.0.0.0:8000"]
