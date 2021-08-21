from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_shelly_engine():
    return create_engine("mysql+mysqlconnector://dbuser:dbpassword@dbserver/ShellyDB", echo=True,pool_recycle=3600)
