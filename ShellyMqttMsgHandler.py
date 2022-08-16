import json
import logging

import paho.mqtt.client as mqtt
from sqlalchemy.orm import sessionmaker

from Model import *

AnnounceTopic = "shellies/announce"

Base = declarative_base()
engine = DbConnection.create_shelly_engine()

# create tables
Base.metadata.create_all(engine)


class ShellyMqttMsgHandler(mqtt.Client):

    def __init__(self, client_id="", clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport="tcp"):
        super().__init__(client_id, clean_session, userdata, protocol, transport)
        self.logger = logging.getLogger(__name__)
        self.enable_logger(self.logger)

    def on_connect(self, mqttc, obj, flags, rc):
        self.logger.debug("rc: " + str(rc))

    def on_publish(self, mqttc, obj, mid):
        self.logger.debug("mid: " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_message(self, mqttc, obj, msg):
        try:
            # create a Session
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                self.logger.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
                payload = msg.payload.decode("utf-8")
                if msg.topic == AnnounceTopic:
                    self._process_announce(payload, session)
                elif msg.topic.find("shellies/") != -1 and msg.topic.find("/relay/") != -1:
                    deviceId = msg.topic[len("shellies/"):msg.topic.find("/relay/")]
                    device = session.query(Device).filter_by(id=deviceId).first()
                    if device is None:
                        self.logger.warning("nicht registriertes Device: " + deviceId)
                        session.close()
                        return
                    idx = msg.topic.find("/relay/") + len("/relay/")
                    channelId = int(msg.topic[idx:idx + 1])
                    series = session.query(Series).filter_by(dbIdDevice=device.dbid).order_by(
                        Series.startTimestamp.desc()).first()
                    self.logger.debug("device " + str(device.dbid))
                    self.logger.debug("channelId " + str(channelId))
                    if series is None:
                        self._create_new_series(device, session)
                        session.commit()
                    self.logger.debug("series " + str(series.dbid))

                    channel = session.query(Channel).filter_by(series=series).filter_by(channelId=channelId).first()

                    if channel is None:
                        channel = Channel(series, channelId, 0)
                        session.add(channel)
                        session.commit()
                    self.logger.debug("Channel " + str(channel.channelId))

                    if msg.topic.find("energy") > 0:
                        energy = round(int(payload) / (60.0 * 1000), 3)
                        self._process_energy(energy, device, series, channel, session)
                    elif msg.topic.find("power") > 0:
                        power = float(payload)
                        self._process_power(power, series, channel, session)
                else:
                    self._process_plus(msg.topic, msg.payload, session)
                session.close()
            except Exception as e:
                session.rollback()
                session.close()
                self.logger.warning(e)
                raise e
        except Exception as e:
            self.logger.warning(e)

    def _process_energy(self, energy, device, series, channel, session):
        if int(energy * 1000) < int(channel.energy * 1000):
            self.logger.info("Energy is Lower than db Record -> Create new Series")
            self.logger.info(str(energy) + " " + str(channel.energy))
            series = self._create_new_series(device, session)
            session.commit()
            channel = session.query(Channel).filter_by(series=series).filter_by(channelId=channel.channelId).first()
        if channel is not None:
            channel.energy = energy
            session.commit()
        else:
            self.logger.warning("channel is None (Energy) series: " + str(series.dbid))
        self.logger.debug("process_energy " + str(energy))

    def _process_power(self, power, series, channel, session):
        if channel is not None:
            measurement = Measurement(power, channel)
            session.add(measurement)
            session.commit()
        else:
            self.logger.warning("channel is None (Energy) series: " + str(series.dbid))
        self.logger.debug("process_power " + str(power))

    def _process_announce(self, payload, session):
        d = json.loads(payload)
        device = session.query(Device).filter_by(id=d["id"]).first()
        if device is None:
            device = Device(d["id"], d["model"], d["mac"], d["ip"], d["id"])
            session.add(device)
            self._subscribe_device(device)
            self._create_new_series(device, session)
        else:
            device.ip = d["ip"]

        session.commit()

    def _process_plus(self, topic, payload, session):
        deviceId = topic[0:topic.find("/status/switch")]
        device = session.query(Device).filter_by(id=deviceId).first()
        if device is None:
            self.logger.warning("nicht registriertes Device: " + deviceId)
            return
        idx = topic.find("switch:") + len("switch:")
        channelId = int(topic[idx:idx + 1])
        series = session.query(Series).filter_by(dbIdDevice=device.dbid).order_by(
            Series.startTimestamp.desc()).first()
        self.logger.debug("device " + str(device.dbid))
        self.logger.debug("channelId " + str(channelId))
        if series is None:
            self._create_new_series(device, session)
            session.commit()
        self.logger.debug("series " + str(series.dbid))

        channel = session.query(Channel).filter_by(series=series).filter_by(channelId=channelId).first()

        if channel is None:
            channel = Channel(series, channelId, 0)
            session.add(channel)
            session.commit()
        self.logger.debug("Channel " + str(channel.channelId))

        data = json.loads(payload.decode('utf-8'))

        self._process_energy(data["aenergy"]["total"] / 1000, device, series, channel, session)
        self._process_power(data["apower"], series, channel, session)

    def _create_new_series(self, device, session):
        self.logger.info("Create new series for Device " + device.id)
        series = Series(device)
        session.add(series)
        if device.model == "SHSW-PM":
            channel = Channel(series, 0, 0)
            session.add(channel)
        elif device.model == "SHSW-25":
            channel0 = Channel(series, 0, 0)
            channel1 = Channel(series, 1, 0)
            session.add(channel0)
            session.add(channel1)
        elif device.model == "shellyplus1pm":
            channel = Channel(series, 0, 0)
            session.add(channel)
        return series

    def _subscribe_device(self, device):
        if device.model == "SHSW-PM":
            self.logger.info("Subscribe Shelly 1PM: " + device.id)
            self.subscribe("shellies/" + device.id + "/relay/0/power", 0)
            self.subscribe("shellies/" + device.id + "/relay/0/energy", 0)
        elif device.model == "SHSW-25":
            self.logger.info("Subscribe Shelly 2.5: " + device.id)
            self.subscribe("shellies/" + device.id + "/relay/0/power", 0)
            self.subscribe("shellies/" + device.id + "/relay/1/power", 0)
            self.subscribe("shellies/" + device.id + "/relay/0/energy", 0)
            self.subscribe("shellies/" + device.id + "/relay/1/energy", 0)
        elif device.model == "shellyplus1pm":
            self.logger.info("Subscribe Shelly Plus 1PM: " + device.id)
            self.subscribe(device.id + "/status/switch:0", 0)

    def run(self, username, password, server, port):
        self.logger.info("Connect to MqTT Broker")
        self.username_pw_set(username, password)
        self.connect(server, port, 60, bind_address="")

        self.loop_start()
        self.subscribe(AnnounceTopic, 0)

        # create a Session
        Session = sessionmaker(bind=engine)
        session = Session()

        for device in session.query(Device):
            self._subscribe_device(device)
        session.close()
