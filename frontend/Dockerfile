# =====================================================
# Agent Orchestrator - Frontend Dockerfile
# Platform: linux/amd64 (for Azure deployment)
# Multi-stage build for smaller image
# =====================================================

# Stage 1: Build
FROM --platform=linux/amd64 node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Configure npm for corporate network and install dependencies
RUN npm config set strict-ssl false && \
    npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build argument for API URL
ARG REACT_APP_API_URL=http://localhost:4001
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the application
RUN npm run build

# Stage 2: Production
FROM --platform=linux/amd64 nginx:alpine

# Copy custom nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]

