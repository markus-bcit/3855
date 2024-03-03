from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime

class Workout(Base):
    """ Workout table """

    __tablename__ = "workout"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    startDate = Column(String(50), nullable=False)
    endDate = Column(String(250), nullable=False)
    frequency = Column(Integer, nullable=False)
    dateCreated = Column(String(250), nullable=False)
    traceId = Column(String(250), nullable=False)
    
    def __init__(self, type, startDate, endDate, frequency, traceId):
        self.type = type
        self.startDate = startDate 
        self.endDate = endDate
        self.frequency = frequency
        self.dateCreated = datetime.datetime.now()
        self.traceId = traceId

    def to_dict(self):
        
        return {
            'id': self.id,
            'type': self.type,
            'startDate': self.startDate,
            'endDate': self.endDate,
            'frequency': self.frequency,
            'traceId': self.traceId
        }
    
    