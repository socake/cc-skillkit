FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

ENV DEBIAN_FRONTEND=noninteractive

# Xvfb + lightweight WM + VNC + noVNC + supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        fluxbox \
        novnc \
        websockify \
        supervisor \
        net-tools \
        procps \
        socat \
        vim-tiny \
    && rm -rf /var/lib/apt/lists/*

# noVNC defaults to vnc.html; make an index redirect for convenience
RUN ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Persistent profile dir (mounted by docker-compose)
RUN mkdir -p /profile && chmod 777 /profile

# Stable symlink decoupling the Playwright chromium version number
RUN ln -sf "$(find /ms-playwright -name chrome -executable -type f -path '*chromium*chrome-linux*' | head -1)" /usr/local/bin/chrome

# Startup config
COPY supervisord.conf /etc/supervisor/conf.d/browser-verify.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5900 6080 9222

ENTRYPOINT ["/entrypoint.sh"]
