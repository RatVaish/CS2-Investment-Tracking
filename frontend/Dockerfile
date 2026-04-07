# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Accept build arguments
ARG VITE_API_URL
ARG VITE_STRIPE_PUBLISHABLE_KEY
ARG VITE_STRIPE_MONTHLY_PRICE_ID
ARG VITE_STRIPE_ANNUAL_PRICE_ID

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_STRIPE_PUBLISHABLE_KEY=$VITE_STRIPE_PUBLISHABLE_KEY
ENV VITE_STRIPE_MONTHLY_PRICE_ID=$VITE_STRIPE_MONTHLY_PRICE_ID
ENV VITE_STRIPE_ANNUAL_PRICE_ID=$VITE_STRIPE_ANNUAL_PRICE_ID

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
