FROM debian:13.1

RUN apt-get update \
  && apt-get install -y \
    unixodbc-dev \
    python3 \
    python3-sqlalchemy \
    python3-paho-mqtt \
    python3-pymysql
RUN mkdir /usr/src/app
WORKDIR /usr/src/app

COPY DbConnection.py /usr/src/app/
COPY Model.py /usr/src/app/
COPY ShellyMqttMsgHandler.py /usr/src/app/
COPY main.py /usr/src/app/
COPY logging.json /usr/src/app/

ENV PYTHONUNBUFFERED 1

CMD ["/usr/bin/python3", "main.py"]