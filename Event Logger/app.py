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
from workout_stats import events
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


def get_events():
    logger.info("Request for statistics has started")

    session = DB_SESSION()

    current_stats = session.query(events).order_by(
        events.last_update.desc()).first()

    if current_stats:
        stats_dict = {
            "0001": current_stats.one,
            "0002": current_stats.two,
            "0003": current_stats.three,
            "0004": current_stats.four,
            "last_update": current_stats.last_update
        }
        logger.debug("Current statistics: %s", stats_dict)
        logger.info("Request for statistics has completed")
        session.close()
        return stats_dict, 200
    else:
        logger.error("Statistics do not exist")
        logger.info("Request for statistics has completed")
        session.close()
        return "Statistics do not exist", 404


def populate_events():
    logger.info("Periodic processing has started")
    
    session = DB_SESSION()

    current_stats = session.query(events).order_by(
        events.last_update.desc()).first()
    if current_stats:
        one = current_stats.one
        two = current_stats.two
        three = current_stats.three
        four = current_stats.four
        last_update = current_stats.last_update
    else:
        one = 0
        two = 0
        three = 0
        four = 0
        last_update = datetime.datetime.now()

    current_datetime = datetime.datetime.now()


    req_workout = requests.get(app_config['eventstore']['url'] + '/workout', params={'start_timestamp': last_update.strftime(
        "%Y-%m-%dT%H:%M:%S"), 'end_timestamp': current_datetime.strftime("%Y-%m-%dT%H:%M:%S")})
    req_workout_log = requests.get(app_config['eventstore']['url'] + '/workout/log', params={'start_timestamp': last_update.strftime(
        "%Y-%m-%dT%H:%M:%S"), 'end_timestamp': current_datetime.strftime("%Y-%m-%dT%H:%M:%S")})
    workout_data = req_workout.json()
    workout_log_data = req_workout_log.json()

    if (req_workout_log not in [200, 201]) or (req_workout_log not in [200, 201]):
        logger.info('Workout events: %s - Workout Log events: %s',
                    len(workout_data), len(workout_log_data))
        if len(workout_log_data) >= 1:
            for x in workout_log_data:
                logger.debug(
                    'Workout Log event being processed, trace ID: %s', x['traceId'])
        if len(workout_data) >= 1:
            for x in workout_data:
                logger.debug(
                    'Workout event being processed, trace ID: %s', x['traceId'])
    else:
        logger.error('Workout returned: %s - Workout Log returned: %s',
                     req_workout.status_code, req_workout_log.status_code)

    num_workouts = num_workouts + len(workout_data)
    num_workout_logs = num_workout_logs + len(workout_log_data)
    frequencies = [entry['frequency'] for entry in workout_data]
    if frequencies:
        one = max(frequencies)
        two = min(frequencies)
    else:
        max_freq_workout = 0
        min_freq_workout = 0

    new_stats = events(
        one=one,
        two=two,
        three=three,
        four=four,
        last_update=current_datetime
    )
    session.add(new_stats)
    session.commit()

    logger.debug("Updated statistics ID: %s", new_stats.id)

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



def process_messages():
    try:
        client = create_kafka_client()
        topic = client.topics[str.encode(app_config["events"]["topic"])]

        consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                             reset_offset_on_start=False,
                                             auto_offset_reset=OffsetType.LATEST)
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            logger.info("Message: %s", msg)
            consumer.commit_offsets()
    except Exception as e:
        logger.error('Error processing messages: %s', str(e))


def init_scheduler():
    sched = BackgroundScheduler(daemon=True, timezone='America/Los_Angeles')
    sched.add_job(populate_events, 'interval', seconds=5)
    sched.start()


# Initialize the Flask app
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8120, host='0.0.0.0')
