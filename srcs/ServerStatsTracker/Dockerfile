FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY . .

# Install dependencies
RUN npm ci

# Build the application
RUN npm run build

# Expose port for the application
EXPOSE 5000

# Set environment variables
# ENV NODE_ENV=production

# Run the application
CMD ["npm", "run", "dev"]
