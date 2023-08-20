# FROM node:18-bullseye-slim as browserDownloader
# WORKDIR /usr/src/app
# RUN npm install -g @puppeteer/browsers
# RUN browsers install chrome@114.0.5735.133


FROM python:3.11.4-slim-bullseye
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
# RUN playwright install --with-deps firefox
RUN apt update && apt install -y chromium chromium-driver
COPY . .
# COPY --from=browserDownloader /usr/src/app/chrome/linux*/ ./
COPY ./chromedriver_linux64 ./chromedriver
CMD [ "python3", "./go-crunchy.py" ]