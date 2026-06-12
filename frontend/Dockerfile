# ── Development stage ─────────────────────────────────────────
FROM node:20-alpine AS development

WORKDIR /app
COPY package.json .
RUN npm install
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]

# ── Build stage ───────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install
COPY . .

ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Production stage (Nginx serving static files) ─────────────
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.prod.conf.template /etc/nginx/conf.d/default.conf.template

EXPOSE 8080
# envsubst substitutes only ${PORT} and ${BACKEND_URL}, leaving nginx
# variables like $uri and $host untouched.
CMD ["/bin/sh", "-c", "envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
