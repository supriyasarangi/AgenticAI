FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY tsconfig.json tsconfig.node.json vite.config.ts ./
COPY tailwind.config.js postcss.config.js ./
COPY index.html ./
COPY src ./src

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
