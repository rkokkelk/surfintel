FROM node:20-slim

WORKDIR /app

# NEXT_PUBLIC_* vars are inlined into the JS bundle at build time, and all
# data-fetching here happens in the browser (client components) — so this
# must be a URL the browser can reach (the published host port), not the
# docker-compose service name.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY package.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
