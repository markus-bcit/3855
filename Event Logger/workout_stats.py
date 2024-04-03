from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime

class WorkoutStats(Base):
    """ Workout table """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    one = Column(Integer, nullable=False)
    two = Column(Integer, nullable=False)
    three = Column(Integer, nullable=False)
    four = Column(Integer, nullable=False)
    last_update = Column(DateTime, nullable=False)

    
    def __init__(self, one, two, three, four, last_update):
        self.one = one
        self.two = two 
        self.three = three
        self.four = four
        self.last_update = last_update

    def to_dict(self):
        
        return {
            'id': self.id,
            '0001': self.num_workouts,
            '0002': self.num_workout_logs,
            '0003': self.max_freq_workout,
            '0004': self.min_freq_workout,
            'last_update': self.last_update.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    