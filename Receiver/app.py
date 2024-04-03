from connexion import NoContent
from pykafka import KafkaClient

import requests
import json
import connexion
import yaml
import logging
import logging.config
import uuid
import datetime

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def create_workout(body):
    event = uuid.uuid4()
    trace = uuid.uuid4()
    logger.info('Received event %s request with a trace id of %s', event, trace)
    body['traceId'] = str(trace)
    body['eventId'] = str(event)

    # Kafka producer setup
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()

    # Message to be sent to Kafka
    msg = {
        "type": "workout",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)

    # Publish message to Kafka topic
    producer.produce(msg_str.encode('utf-8'))

    logger.info('Returned event create_workout %s response (Id: %s) with status %s',
                event, trace, 200)
    return NoContent, 201


def log_workout(body):
    event = uuid.uuid4()
    trace = uuid.uuid4()
    logger.info('Received event %s request with a trace id of %s', event, trace)
    body['traceId'] = str(trace)
    body['eventId'] = str(event)

    # Kafka producer setup
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()

    # Message to be sent to Kafka
    msg = {
        "type": "workoutlog",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)

    # Publish message to Kafka topic
    producer.produce(msg_str.encode('utf-8'))

    logger.info('Returned event log_workout %s response (Id: %s) with status %s',
                event, trace, 200)
    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    # Publishing message to event_log topic after successful start and Kafka connection
    try:
        # Kafka producer setup
        client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
        topic = client.topics[str.encode(app_config['events']['topic2'])]
        producer = topic.get_sync_producer()

        # Message indicating Receiver is ready
        ready_msg = {
            "type": "startup",
            "message": "Receiver is ready to receive messages on its RESTful API",
            "code": "0001"
        }
        ready_msg_str = json.dumps(ready_msg)

        # Publish message to event_log topic
        producer.produce(ready_msg_str.encode('utf-8'))
        logger.info('Published message to event_log topic: %s', ready_msg_str)
    except Exception as e:
        logger.error('Error publishing message to event_log topic: %s', str(e))

    app.run(port=8080)
