import yaml
import logging
import logging.config
import uuid
import requests
import datetime
import time
import json

import connexion
from threading import Thread
from pykafka import KafkaClient
from pykafka.common import OffsetType
from connexion import NoContent
from pykafka import KafkaClient
from starlette.middleware.cors import CORSMiddleware
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from base import Base
from workout_stats import Anomaly
from base import Base
from apscheduler.schedulers.background import BackgroundScheduler

import pytz
timezone = pytz.timezone('America/Los_Angeles')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def get_anomaly_stats():
    logger.info("Request for event logger has started")

    session = DB_SESSION()

    current_anomaly = session.query(Anomaly).order_by(
        Anomaly.date_created.desc()).first()
    

    dic = current_anomaly.to_dict()
    out = {}
    out['num_anomalies'] = session.query(Anomaly).count()
    out['most_recent_desc'] = dic['description']
    out['most_recent_datetime'] = dic['date_created']
    out['workout'] = session.query(Anomaly).filter(Anomaly.event_type=='workout').count()
    out['workout_log'] = session.query(Anomaly).filter(Anomaly.event_type=='workoutlog').count()

    if current_anomaly:
        logger.debug("Current statistics: %s", current_anomaly.to_dict())
        logger.info("Request for statistics has completed")
        session.close()
        return out, 200
    else:
        logger.error("Statistics do not exist")
        logger.info("Request for statistics has completed")
        session.close()
        return "Statistics do not exist", 404


def populate_anomaly():
    logger.info("Periodic processing for event logger has started")

    session = DB_SESSION()
    new_anomaly = None
    event_id = ''
    trace_id = ''
    event_type = ''
    anomaly_type = ''
    description = ''

    client = create_kafka_client()
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=False, auto_offset_reset=OffsetType.LATEST)
    logger.info("Retrieving Event Logger")
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg.get('type') == 'workout':
                payload = msg.get('payload')
                if payload.get('frequency') > app_config["threshold"]["workout"]:
                    event_id = payload.get('eventId')
                    trace_id = payload.get('traceId')
                    event_type = 'workout'
                    description = f"Workout frequency of {payload.get('frequency')} greater than threshold of {app_config['threshold']['workout']}"
                    anomaly_type = 'workout'
                    if not session.query(Anomaly).filter_by(event_id=event_id).first():
                        new_anomaly = Anomaly(
                            event_id=event_id,
                            trace_id=trace_id,
                            event_type=event_type,
                            description=description,
                            anomaly_type=anomaly_type)

                        session.add(new_anomaly)
                        session.commit()
            elif msg.get('type') == 'workoutlog':
                payload = msg.get('payload')
                exercises = json.loads(payload.get('exercises'))
                if len(exercises) > app_config["threshold"]["workout"]:


                    event_id = payload.get('eventId')
                    trace_id = payload.get('traceId')
                    event_type = 'workoutlog'
                    description = f"Exercises count of {len(exercises)} greater than threshold of {app_config['threshold']['workout']}"
                    anomaly_type = 'workoutlog'
                    if not session.query(Anomaly).filter_by(event_id=event_id).first():
                        new_anomaly = Anomaly(
                            event_id=event_id,
                            trace_id=trace_id,
                            event_type=event_type,
                            description=description,
                            anomaly_type=anomaly_type)

                        session.add(new_anomaly)
                        session.commit()
                        logger.debug("Updated statistics ID: %s", new_anomaly.id)
            logger.info(
                f"Consumed Code: {msg.get('code')} Message: {msg.get('message')}")
    except:
        logger.error("No more messages found")

    if new_anomaly:
        logger.debug("Updated statistics ID: %s", new_anomaly.id)
    else:
        logger.debug("No new anomaly found")

    session.close()

    logger.info("Periodic processing has ended")


def create_kafka_client():
    max_retries = app_config['kafka']['max_retries']
    retry_count = 0
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    while retry_count < max_retries:
        try:
            logging.info(
                f"Attempting to connect to Kafka, retry {retry_count}")
            client = KafkaClient(hosts=hostname)
            return client
        except Exception as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(5)
            retry_count += 1
    raise Exception("Failed to connect to Kafka after maximum retries")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True, timezone='America/Los_Angeles')
    sched.add_job(populate_anomaly, 'interval', seconds=5)
    sched.start()


# Initialize the Flask app
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", base_path="/anomaly_detector",
            strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8130, host='0.0.0.0')
