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
    logger.info("Request for event logger has started")

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
    logger.info("Periodic processing for event logger has started")

    session = DB_SESSION()

    current_datetime = datetime.datetime.now()

    new_one = 0
    new_two = 0
    new_three = 0
    new_four = 0

    client = create_kafka_client()
    topic = client.topics[str.encode(app_config["events"]["topic2"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving Event Logger")
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg.get('code') == '0001':
                new_one += 1
            elif msg.get('code') == '0002':
                new_two += 1
            elif msg.get('code') == '0003':
                new_three += 1
            elif msg.get('code') == '0004':
                new_four += 1
    except:
        logger.error("No more messages found")

    new_stats = events(
        one=new_one,
        two=new_two,
        three=new_three,
        four=new_four,
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


def init_scheduler():
    sched = BackgroundScheduler(daemon=True, timezone='America/Los_Angeles')
    sched.add_job(populate_events, 'interval', seconds=5)
    sched.start()


# Initialize the Flask app
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", base_path="/event_logger", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8120, host='0.0.0.0')
