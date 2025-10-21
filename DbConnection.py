from sqlalchemy import create_engine
import os

def create_shelly_engine():
    dbUser = os.environ.get('MYSQL_USER')
    dbPassword = os.environ.get('MYSQL_PASSWORD')
    dbServer = os.environ.get('MYSQL_SERVER')
    dbDatabase = os.environ.get('MYSQL_DB')
    dbString = "mysql+pymysql://{}:{}@{}/{}".format(dbUser,dbPassword,dbServer,dbDatabase)
    return create_engine(dbString, echo=True,pool_recycle=3600)
