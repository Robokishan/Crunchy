FROM python:3.11.4-slim-bullseye
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
RUN ["chmod", "+x", "./wait-for-it.sh"]