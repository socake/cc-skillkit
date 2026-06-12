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
        autocutsel \
        xclip \
        xsel \
    && rm -rf /var/lib/apt/lists/*

# noVNC defaults to vnc.html; make an index redirect for convenience
RUN ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Hide noVNC's "normal" status bar (the green "connected" banner covers Chrome's
# address bar); errors and warnings still show.
RUN printf '\n/* hide normal status bar to avoid covering Chrome address bar */\n#noVNC_status.noVNC_status_normal { display: none !important; }\n' \
    >> /usr/share/novnc/app/styles/base.css

# Persistent profile dir (mounted by docker-compose)
RUN mkdir -p /profile && chmod 777 /profile

# fluxbox decorates windows by default, pushing Chrome's tab bar out of the
# viewport; disable decorations globally and pin the window to the top-left.
RUN mkdir -p /root/.fluxbox && cat > /root/.fluxbox/apps <<'EOF'
[app] (name=.*) (class=.*)
  [Deco]        {NONE}
  [Position]    (UPPERLEFT)     {0 0}
  [Dimensions]  {1440 900}
  [Maximized]   {yes}
[end]
EOF

# Stable symlink decoupling the Playwright chromium version number
RUN ln -sf "$(find /ms-playwright -name chrome -executable -type f -path '*chromium*chrome-linux*' | head -1)" /usr/local/bin/chrome

# Startup config
COPY supervisord.conf /etc/supervisor/conf.d/browser-verify.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5900 6080 9222

ENTRYPOINT ["/entrypoint.sh"]
