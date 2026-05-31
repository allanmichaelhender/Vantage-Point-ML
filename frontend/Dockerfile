FROM node:20-slim AS build
WORKDIR /build
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /project/frontend
COPY --from=build /build/dist ./dist
COPY --from=build /build/node_modules ./node_modules
COPY package.json ./
EXPOSE 5173

# Local dev: source is bind-mounted from host, dist/ is pre-baked in image
CMD ["npm", "run", "dev", "--", "--host"]
