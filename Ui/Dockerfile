# build environment (UI + Notion API server)
FROM node:24.11.0-alpine AS deps
WORKDIR /opt/app
RUN apk add --no-cache bash && corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:24.11.0-alpine AS builder
WORKDIR /opt/app
RUN apk add --no-cache bash && corepack enable

COPY . .
COPY --from=deps /opt/app/node_modules ./node_modules

ENV NODE_ENV=production
# Vite build (frontend) + TypeScript compile (server to JS)
RUN pnpm vite build && pnpm build:server

FROM node:24.11.0-alpine AS runner
WORKDIR /opt/app
RUN apk add --no-cache bash && corepack enable

COPY --from=builder /opt/app/dist ./dist
COPY --from=builder /opt/app/dist-server/server ./server
COPY --from=builder /opt/app/dist-server/src ./src
COPY --from=builder /opt/app/package.json ./package.json
COPY --from=builder /opt/app/pnpm-lock.yaml ./pnpm-lock.yaml

RUN pnpm install --frozen-lockfile --ignore-scripts --prod

EXPOSE 80
ENV PORT=80
ENV NODE_ENV=production

CMD ["node", "server/index.js"]