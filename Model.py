from sqlalchemy import *
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.dialects import postgresql, mysql, mssql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

import DbConnection

Base = declarative_base()
engine = DbConnection.create_shelly_engine()


class Device(Base):
    """"""
    __tablename__ = "Device"

    dbid = Column(Integer, primary_key=True)
    id = Column(String(30), nullable=False)
    model = Column(String(20), nullable=False)
    mac = Column(String(30))
    ip = Column(String(40))
    name = Column(String(40), nullable=True)

    series = relationship("Series",foreign_keys='Series.dbIdDevice', back_populates="device")

    # ----------------------------------------------------------------------
    def __init__(self, id, model, mac, ip, name):
        """"""
        self.id = id
        self.model = model
        self.mac = mac
        self.ip = ip
        self.name = name


class Series(Base):
    """"""
    __tablename__ = "Series"

    dbid = Column(Integer, primary_key=True)
    startTimestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    dbIdDevice = Column(Integer, ForeignKey(Device.dbid), nullable=False)

    device = relationship('Device', foreign_keys='Series.dbIdDevice', back_populates="series")

    # ----------------------------------------------------------------------
    def __init__(self, device):
        """"""
        self.device = device


class Channel(Base):
    """"""
    __tablename__ = "Channel"

    dbid = Column(Integer, primary_key=True)
    dbIdSeries = Column(Integer, ForeignKey(Series.dbid), nullable=False)
    energy = Column(Float, nullable=True)
    channelId = Column(Integer, nullable=False)

    series = relationship('Series', foreign_keys='Channel.dbIdSeries')

    # ----------------------------------------------------------------------
    def __init__(self, series, channelId, energy):
        """"""
        self.series = series
        self.channelId = channelId
        self.energy = energy


class Measurement(Base):
    """"""
    __tablename__ = "Measurement"

    dbid = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    value = Column(Float, nullable=False)
    dbIdChannel = Column(Integer, ForeignKey(Channel.dbid), nullable=False)

    channel = relationship('Channel', foreign_keys='Measurement.dbIdChannel')

    # ----------------------------------------------------------------------
    def __init__(self, value, channel):
        """"""
        self.value = value
        self.channel = channel

Base.metadata.create_all(engine)