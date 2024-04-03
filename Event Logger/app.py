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


