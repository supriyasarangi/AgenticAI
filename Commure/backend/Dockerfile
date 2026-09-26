FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY src ./src
COPY tsconfig.json .

EXPOSE 5000

CMD ["npm", "run", "dev"]
