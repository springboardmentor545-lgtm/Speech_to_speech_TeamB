# Stage 1: Build the React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies using npm ci for deterministic builds
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Build the application for production
# Any build-time environment variables should be passed here using ARG and ENV
# ARG VITE_API_URL
# ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Serve the built application with Nginx
FROM nginx:1.25-alpine

# Copy the built artifacts from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom Nginx configuration
# Ensure nginx.conf exists in the frontend directory
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose ports (80 for HTTP, 443 for HTTPS if configured)
EXPOSE 80
# EXPOSE 443

# Healthcheck for Nginx (optional but good practice)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3     CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Command to start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
