from connexion import NoContent
from pykafka import KafkaClient
import yaml
import logging
import logging.config
import uuid
import datetime
import json
import time

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

client = None
producer = None

def create_kafka_client():
    max_retries = app_config['kafka']['max_retries']
    retry_count = 0
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    while retry_count < max_retries:
        try:
            logging.info(f"Attempting to connect to Kafka, retry {retry_count}")
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            return client, topic
        except Exception as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(5)  
            retry_count += 1
    raise Exception("Failed to connect to Kafka after maximum retries")

def initialize_producer():
    global producer
    global client
    client, topic = create_kafka_client()
    producer = topic.get_sync_producer()

def create_workout(body):
    global producer
    if producer is None:
        initialize_producer()

    event = uuid.uuid4()
    trace = uuid.uuid4()
    logger.info('Received event %s request with a trace id of %s', event, trace)
    body['traceId'] = str(trace)
    body['eventId'] = str(event)
    msg = {"type": "workout",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info('Returned event create_workout %s response (Id: %s) with status %s',
                event, trace, 200)
    return NoContent, 201

def log_workout(body):
    global producer
    if producer is None:
        initialize_producer()

    event = uuid.uuid4()
    trace = uuid.uuid4()
    logger.info('Received event %s request with a trace id of %s', event, trace)
    body['traceId'] = str(trace)
    body['eventId'] = str(event)
    msg = {"type": "workoutlog",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info('Returned event log_workout %s response (Id: %s) with status %s',
                event, trace, 200)
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)
