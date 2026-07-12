# Grok-in-cage: extend agent-cage-agent with Grok CLI.
# Binary is copied to /usr/local/bin so a mounted auth-only volume does not hide it.
# Auth: mount auth.json at /home/agent/.grok/auth.json at runtime (OIDC session).
#
ARG BASE_IMAGE=agent-cage-agent:latest
FROM ${BASE_IMAGE}

USER agent
WORKDIR /home/agent
ENV HOME=/home/agent
ENV GROK_HOME=/home/agent/.grok
ENV GROK_BIN_DIR=/home/agent/.local/bin

# Install into user home, then copy real binary to a path not covered by auth mounts
USER root
RUN mkdir -p /home/agent/.grok /home/agent/.local/bin \
    && chown -R agent:agent /home/agent/.grok /home/agent/.local

USER agent
RUN curl -fsSL https://x.ai/cli/install.sh | bash \
    && GROK_REAL="$(readlink -f /home/agent/.local/bin/grok 2>/dev/null || readlink -f /home/agent/.grok/bin/grok)" \
    && test -n "$GROK_REAL" && test -x "$GROK_REAL" \
    && cp -a "$GROK_REAL" /tmp/grok-bin \
    && /tmp/grok-bin --version

USER root
RUN install -m 0755 /tmp/grok-bin /usr/local/bin/grok \
    && ln -sfn /usr/local/bin/grok /usr/local/bin/agent \
    && rm -f /tmp/grok-bin \
    && /usr/local/bin/grok --version

# Keep a writable .grok for auth.json (file mount target directory)
RUN mkdir -p /home/agent/.grok && chown -R agent:agent /home/agent/.grok

ENV PATH="/usr/local/bin:/home/agent/.local/bin:${PATH}"
WORKDIR /workspace
USER agent
