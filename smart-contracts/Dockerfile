FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy contract files
COPY . .

# Compile contracts
RUN npx hardhat compile

EXPOSE 8546

CMD ["npx", "hardhat", "node", "--hostname", "0.0.0.0", "--port", "8546"]
