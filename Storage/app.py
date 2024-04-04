import time
import connexion
from connexion import NoContent
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from base import Base
from workout import Workout
from workout_log import WorkoutLog
from base import Base
import uuid
import datetime
import yaml
import logging
import logging.config
import datetime
import json

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.debug("Conneting to DB. Hostname: %s,  Port %s",
             app_config['datastore']['hostname'], app_config['datastore']['port'])
DB_ENGINE = create_engine(
    f"mysql+pymysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}", 
    pool_size=10,
    pool_recycle=300,
    pool_pre_ping=True)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def create_workout(body):
    session = DB_SESSION()
    w = Workout(body['type'],
                body['startDate'],
                body['endDate'],
                body['frequency'],
                body['traceId'])
    session.add(w)
    session.commit()
    session.close()

    logger.debug("Stored event %s request with a trace id of %s",
                 body['eventId'], body['traceId'])
    return NoContent, 201


def log_workout(body):
    session = DB_SESSION()

    wl = WorkoutLog(body['workoutId'],
                    body['userId'],
                    body['startDate'],
                    body['endDate'],
                    str(body['exercises']),
                    body['traceId'])

    session.add(wl)
    session.commit()
    session.close()

    logger.debug("Stored event %s request with a trace id of %s",
                 body['eventId'], body['traceId'])
    return NoContent, 201


def get_workout(start_timestamp=None, end_timestamp=None):
    """ Gets new workouts created between the start and end timestamps """
    if (start_timestamp is None) or (end_timestamp is None):
        return [], 201
    else:
        start_timestamp_datetime = datetime.datetime.strptime(
            start_timestamp, "%Y-%m-%dT%H:%M:%S")
        end_timestamp_datetime = datetime.datetime.strptime(
            end_timestamp, "%Y-%m-%dT%H:%M:%S")
    session = DB_SESSION()

    results = session.query(Workout).filter(and_(
        Workout.dateCreated >= start_timestamp_datetime, Workout.dateCreated < end_timestamp_datetime))
    results_list = []
    for workout in results:
        results_list.append(workout.to_dict())
    session.close()

    logger.info("Query for Workout Log readings after %s returns %d results" % (
        start_timestamp, len(results_list)))
    return results_list, 200


def get_workout_log(start_timestamp=None, end_timestamp=None):
    """ Gets new workouts created between the start and end timestamps """
    if (start_timestamp is None) or (end_timestamp is None):
        return [], 201
    else:
        start_timestamp_datetime = datetime.datetime.strptime(
            start_timestamp, "%Y-%m-%dT%H:%M:%S")
        end_timestamp_datetime = datetime.datetime.strptime(
            end_timestamp, "%Y-%m-%dT%H:%M:%S")
    session = DB_SESSION()

    results = session.query(WorkoutLog).filter(and_(
        WorkoutLog.dateCreated >= start_timestamp_datetime, WorkoutLog.dateCreated < end_timestamp_datetime))
    results_list = []
    for workout_log in results:
        results_list.append(workout_log.to_dict())
    return results_list, 200


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


def publish_ready_message():
    try:
        client = create_kafka_client()
        topic = client.topics[str.encode(app_config["events"]["topic2"])]
        producer = topic.get_sync_producer()

        ready_msg = {
            "type": "startup",
            "message": "Receiver is ready to consume messages from the events topic",
            "code": "0002",
            "id": f"{uuid.uuid4()}"
        }
        ready_msg_str = json.dumps(ready_msg)

        producer.produce(ready_msg_str.encode('utf-8'))
        logger.info('Published message to event_log topic: %s', ready_msg_str)
    except Exception as e:
        logger.error('Error publishing message to event_log topic: %s', str(e))


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
            payload = msg["payload"]
            if msg["type"] == "workout":  # Change this to your event type
                # Store the event1 (i.e., the payload) to the DB
                create_workout(payload)
            elif msg["type"] == "workoutlog":  # Change this to your event type
                # Store the event2 (i.e., the payload) to the DB
                log_workout(payload)
            consumer.commit_offsets()
    except Exception as e:
        logger.error('Error processing messages: %s', str(e))

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    t1 = Thread(target=process_messages, daemon=True)
    t1.start()

    publish_ready_message()

    app.run(port=8090)