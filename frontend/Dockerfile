FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN rm -f package-lock.json && npm install

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=2025

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./

EXPOSE 2025

CMD ["node", "build"]
