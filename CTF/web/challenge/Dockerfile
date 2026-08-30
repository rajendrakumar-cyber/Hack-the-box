FROM oven/bun:1-alpine AS build

WORKDIR /app

COPY app/package.json ./package.json
RUN bun install

COPY app/ ./
RUN bun run build

FROM oven/bun:1-alpine

RUN apk add --no-cache nginx supervisor \
  && mkdir -p /run/nginx

WORKDIR /app

COPY app/package.json ./package.json
RUN bun install --production

COPY app/index.ts ./index.ts
COPY --from=build /app/dist ./dist
COPY flag.txt /flag.txt
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/supervisord.conf /etc/supervisord.conf

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
