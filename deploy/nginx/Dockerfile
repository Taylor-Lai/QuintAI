FROM node:22-bookworm-slim AS web-builder

WORKDIR /build/web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY frontend/ ./
ENV VITE_API_BASE_URL=/api
RUN npm run build


FROM nginx:1.28-alpine

COPY --from=web-builder /build/web/dist /usr/share/nginx/html
COPY deploy/nginx/app-locations.conf /etc/nginx/includes/app-locations.conf
COPY deploy/nginx/http.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
