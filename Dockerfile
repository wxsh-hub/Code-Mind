# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

# Define build argument for optional dependencies
# Comma-separated list, e.g., "presidio,xetrack"
ARG INSTALL_EXTRAS=""

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
# This might be needed if using volumes in certain CI/CD environments
# ENV UV_LINK_MODE=copy

# Install the project's base dependencies using pyproject.toml
# We install dependencies first without the project code for better caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    # Optional: Add uv.lock if you use it
    # --mount=type=bind,source=uv.lock,target=uv.lock \
    # Install only dependencies defined in pyproject.toml (no extras yet)
    uv sync --no-dev --no-editable --no-install-project

# Then, add the rest of the project source code
COPY . /app

# Install the project itself, including specified optional dependencies
# Using pip install here as it directly supports the extras syntax.
RUN --mount=type=cache,target=/root/.cache/uv \
    EXTRA_SPECIFIER="" && \
    if [ -n "$INSTALL_EXTRAS" ]; then EXTRA_SPECIFIER="[${INSTALL_EXTRAS}]"; fi && \
    echo "Installing project with extras: .${EXTRA_SPECIFIER}" && \
    uv pip install --system ".${EXTRA_SPECIFIER}"

# --- Final runtime image ---
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install Node.js and npm (which includes npx)
# Need curl, gnupg for adding nodesource repo
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    # Clean up apt lists to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Verify installations (optional)
RUN node --version
RUN npm --version
RUN npx --version

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy the virtual environment from the builder stage
COPY --from=uv /usr/local/bin/ /usr/local/bin/
COPY --from=uv /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

# Copy the application code
COPY --chown=appuser:appuser . /app

# Make Python output unbuffered
ENV PYTHONUNBUFFERED=1

# Set the entrypoint to the mcp-gateway command
# Arguments should be passed via `docker run`
ENTRYPOINT ["mcp-gateway"] 