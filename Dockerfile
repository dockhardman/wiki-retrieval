FROM python:3.8-slim

LABEL maintainer="dockhardman <f1470891079@gmail.com>"

# Install Dependencies
WORKDIR /
COPY ./requirements.txt ./requirements.txt
RUN pip install -r /requirements.txt

# Application
WORKDIR /app/
COPY ./app /app

CMD ["bash", "/app/start.sh"]
