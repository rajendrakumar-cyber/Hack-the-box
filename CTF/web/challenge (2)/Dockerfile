FROM node:22-trixie-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates nginx supervisor \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/package*.json ./
RUN npm install --omit=dev \
  && npx playwright install --with-deps firefox \
  && npm cache clean --force \
  && rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY bot ./bot
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY flag.txt /flag.txt
COPY entrypoint.js /app/entrypoint.js
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 80

CMD ["/entrypoint.sh"]
