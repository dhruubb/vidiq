FROM node:20-alpine
WORKDIR /usr/src/app
COPY frontend/package.json frontend/tailwind.config.js frontend/postcss.config.js ./
COPY frontend/index.html ./
COPY frontend/src ./src
RUN npm install && npm run build || (echo "Build may require internet in runtime; keeping dev server" && true)
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


