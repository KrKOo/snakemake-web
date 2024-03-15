FROM node:20-alpine as build

WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
ENV VITE_API_URL /api

COPY ./web/package.json ./web/package-lock.json ./
RUN npm install

COPY ./web ./
RUN npm run build

FROM python:3.12
WORKDIR /app

ENV FLASK_ENV production

COPY --from=build /app/dist ./web
RUN mkdir ./api

COPY ./server/requirements.txt ./api
RUN pip install -r ./api/requirements.txt

COPY ./server ./api
WORKDIR /app/api
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "--interface", "wsgi" ,"run:app"]
