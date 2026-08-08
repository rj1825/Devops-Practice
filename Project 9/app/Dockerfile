# Stage 1: Build dependencies
FROM node:18-alpine AS builder
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Production release
FROM node:18-alpine
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/node_modules ./node_modules
COPY . .

# Security Best Practice: Run container as non-root user
USER node

EXPOSE 3000
CMD ["npm", "start"]
