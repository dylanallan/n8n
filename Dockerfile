FROM node:20.15-alpine

RUN apk add --update python3 make g++ && rm -rf /var/cache/apk/*

WORKDIR /app

COPY package.json ./
COPY railway.toml ./

RUN corepack enable && corepack prepare pnpm@10.2.1 --activate

RUN pnpm install --frozen-lockfile

ENV NODE_ENV=production
ENV N8N_USER_MANAGEMENT_DISABLED=true
ENV DB_TYPE=postgresdb

EXPOSE 5678

CMD ["pnpm", "start"] 