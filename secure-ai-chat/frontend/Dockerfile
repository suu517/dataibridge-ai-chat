# ==============================================================================
# Secure AI Chat - Frontend Dockerfile (Production)
# Multi-stage build for optimized static file serving
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Stage (if needed for future SPA framework)
# ------------------------------------------------------------------------------
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files (future use for npm-based build)
# COPY package*.json ./
# RUN npm ci --only=production

# For now, just copy static files
COPY public/ ./public/

# ------------------------------------------------------------------------------
# Stage 2: Production Nginx Server
# ------------------------------------------------------------------------------
FROM nginx:1.25-alpine as runtime

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy static files from builder stage
COPY --from=builder /app/public /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create non-root user for security
RUN addgroup -g 1001 -S appuser \
    && adduser -S appuser -u 1001 -G appuser

# Set proper permissions
RUN chown -R appuser:appuser /usr/share/nginx/html \
    && chown -R appuser:appuser /var/cache/nginx \
    && chown -R appuser:appuser /var/log/nginx \
    && chown -R appuser:appuser /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R appuser:appuser /var/run/nginx.pid

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]