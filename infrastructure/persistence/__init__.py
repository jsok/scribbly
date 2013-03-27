from sqlalchemy import MetaData

metadata = MetaData()

# Finally import all models so mappings are created
import models