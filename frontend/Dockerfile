# 1. Use a lightweight Node.js image (Node 20+ is standard for Vite)
FROM node:20-alpine

# 2. Set the working directory inside the container
WORKDIR /project

# 3. Copy package files first to leverage Docker's layer caching
# This ensures 'npm install' only runs when dependencies change
COPY package*.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of your React source code
COPY . .

# 6. Vite's default development port
EXPOSE 5173

# 7. Start Vite with --host to allow external access from the Docker bridge
# Without --host, the dev server remains 'invisible' outside the container
CMD ["npm", "run", "dev", "--", "--host"]
