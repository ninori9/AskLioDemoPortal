# ---- Build stage ----
FROM node:20-bookworm-slim AS build
WORKDIR /app

# Copy manifests and force a fresh, Linux-friendly install
COPY package*.json ./
# Avoid the cross-platform optional-deps bug by ignoring the macOS lockfile
RUN rm -f package-lock.json && npm install

# Build app
COPY . .
ARG ANGULAR_ENV=production
RUN npm run build -- --configuration=${ANGULAR_ENV}

# ---- Runtime stage ----
FROM nginx:stable-alpine
# Simple SPA config
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Angular 18 outputs to dist/<proj>/browser
COPY --from=build /app/dist/asklio-portal/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]