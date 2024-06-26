import yaml
import logging
import logging.config
import uuid
import requests
import datetime
import time
import json
import os

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

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
    logger = logging.getLogger('basicLogger')
    logger.info("App Conf File: %s" % app_conf_file)
    logger.info("Log Conf File: %s" % log_conf_file)


DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def get_anomaly_stats():
    """returns the anomaly stats

    Returns:
        dict: dict containing the anomaly stats
    """
    logger.info("Request for anomaly has started")

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
        logger.debug("Current anomaly: %s", out)
        logger.info("Request for anomaly has completed")
        session.close()
        return out, 200
    else:
        logger.error("anomaly do not exist")
        logger.info("Request for anomaly has completed")
        session.close()
        return "anomaly do not exist", 404


def populate_anomaly():
    """populates the anomaly sqlite
    """
    logger.info("Periodic anomaly check for anomalies has started")

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
    logger.info("Retrieving events for anomaly detection")
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
                        logger.debug("Updated anomoly ID: %s", new_anomaly.id)
            elif msg.get('type') == 'workoutlog':
                payload = msg.get('payload')
                exercises = payload.get('exercises')
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
                        logger.debug("Updated anomoly ID: %s", new_anomaly.id)
    except:
        logger.error("No more anomalies found")


    session.close()

    logger.info("Periodic anomaly detection has ended")


def create_kafka_client():
    """connects to Kafka

    Raises:
        Exception: if fails

    Returns:
        client upon successful connection
    """
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
