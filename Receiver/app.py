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
import json

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
    # req = requests.post(app_config['eventstore1']['url'], json=body)
    client = KafkaClient(
        hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()

    msg = {"type": "workout",
           "datetime":
           datetime.datetime.now().strftime(
               "%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
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
    # req = requests.post(app_config['eventstore2']['url'], json=body)

    client = KafkaClient(
        hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()
    msg = {"type": "workoutlog",
           "datetime":
           datetime.datetime.now().strftime(
               "%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    logger.info('Returned event log_workout %s response (Id: %s) with status %s',
                event, trace, 200)
    return NoContent, 201

# def stats():
#     event = uuid.uuid4()
#     trace = uuid.uuid4()
#     body = {}
#     logger.info('Received event %s request with a trace id of %s', event, trace)
#     body['traceId'] = str(trace)
#     body['eventId'] = str(event)
#     req = requests.get(app_config['stats']['url'], json=body)
#     logger.info('Returned event log_workout %s response (Id: %s) with status %s', event, trace, req.status_code)
#     return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    app.run(port=8080)
