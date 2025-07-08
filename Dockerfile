# Multi-stage Docker build for the arbitrage bot

# Python backend stage
FROM python:3.9-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py", "--api-only"]

# Node.js dashboard stage
FROM node:18-alpine as frontend

WORKDIR /app

# Copy package files
COPY dashboard/package*.json ./

# Install dependencies
RUN npm install

# Copy dashboard code
COPY dashboard/ .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Command to run the dashboard
CMD ["npm", "start"]
