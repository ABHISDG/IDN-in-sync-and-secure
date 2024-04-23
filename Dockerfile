FROM python:3.12.1-slim-bullseye

# Install all python dependencies and selenium dependencies
# Most of these are for selenium and the chrome web browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libfontconfig1 \
    libdbus-1-3 \
    libxrender1 \
    libxkbcommon0 \
    xfonts-base \
    xfonts-75dpi \
    xfonts-100dpi \
    xfonts-cyrillic \
    xfonts-scalable \
    fonts-liberation \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
    requests \
    anybadge \
    junit-xml \
    selenium
