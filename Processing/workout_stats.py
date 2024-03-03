from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime

class WorkoutStats(Base):
    """ Workout table """

    __tablename__ = "WorkoutStats"

    id = Column(Integer, primary_key=True)
    num_workouts = Column(Integer, nullable=False)
    num_workout_logs = Column(Integer, nullable=False)
    max_freq_workout = Column(Integer, nullable=False)
    min_freq_workout = Column(Integer, nullable=False)
    last_update = Column(DateTime, nullable=False)

    
    def __init__(self, num_workouts, num_workout_logs, max_freq_workout, min_freq_workout, last_update):
        self.num_workouts = num_workouts
        self.num_workout_logs = num_workout_logs 
        self.max_freq_workout = max_freq_workout
        self.min_freq_workout = min_freq_workout
        self.last_update = last_update

    def to_dict(self):
        
        return {
            'id': self.id,
            'num_workouts': self.num_workouts,
            'num_workout_logs': self.num_workout_logs,
            'max_freq_workout': self.max_freq_workout,
            'min_freq_workout': self.min_freq_workout,
            'last_update': self.last_update.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    