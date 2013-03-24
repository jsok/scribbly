from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Session = sessionmaker()
Base = declarative_base()
metadata = MetaData()

# Finally import all models so mappings are created
import models