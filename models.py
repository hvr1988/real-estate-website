from sqlalchemy import Column, Integer, String
from database import Base

# ADMIN TABLE
class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)


# PROPERTY TABLE (ONLY ONE TIME)
class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    location = Column(String)
    price = Column(String)
    description = Column(String)
    image = Column(String)
