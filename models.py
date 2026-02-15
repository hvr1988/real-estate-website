from sqlalchemy import Column, Integer, String
from database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    location = Column(String)
    price = Column(String)
    description = Column(String)
    image = Column(String)
    category = Column(String)
    status = Column(String, default="Available")
    video_url = Column(String, nullable=True) # NEW: YouTube Link