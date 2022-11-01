from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_apscheduler import APScheduler
from os import getenv
import secrets
import logging

from time import sleep

from dotenv import load_dotenv
from os.path import realpath, dirname
import socket
from datetime import datetime
from rabbitmq_pika_flask import RabbitMQ
import json


logger = logging.getLogger(__name__)
root_dir = realpath(dirname(realpath(__file__)) + "/..")
load_dotenv(dotenv_path=f"{root_dir}/.env")
logging.basicConfig(level=getenv("LOGLEVEL", "INFO").upper())

run_port = getenv("RUN_PORT", 80)
run_host = getenv("RUN_HOST", "0.0.0.0")
is_run_debug = getenv('FLASK_DEBUG', "false").lower() in ['true', '1', 't', 'y', 'yes']

logger.info("")

app = Flask(__name__)

app.config["FLASK_ENV"] = "production" if is_run_debug else "development"
app.config["MQ_URL"] = getenv("AMPQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F?connection_attempts=3&heartbeat=3600")
app.config['MQ_EXCHANGE'] = getenv("AMPQ_EXCHANGE", "exchange")
app.config['MQ_EXCHANGE_TYPE'] = getenv("AMPQ_EXCHANGE_TYPE", "fanout")
logger.info("Using AMPQ_URL='%s' MQ_EXCHANGE='%s'", app.config['MQ_URL'], app.config['MQ_EXCHANGE'])

rabbit = RabbitMQ(app)
rabbit_channel = rabbit.get_connection().channel()
rabbit_channel.exchange_declare(
    exchange=app.config['MQ_EXCHANGE'],
    exchange_type=app.config['MQ_EXCHANGE_TYPE']
)

scheduler = BackgroundScheduler()
flask_scheduler = APScheduler(scheduler)
flask_scheduler.init_app(app)


hostname = socket.gethostname()

message_number = 0


def get_ms_time():
    # microsecond
    return datetime.now().microsecond


@app.get("/")
def home():
    return f"Hello World! It's '{get_ms_time()}' and I am host:'{hostname}'"


def detect():
    # Bias towards 0
    detection_options = [0] + [0] + list(range(0, 8))

    # ===Random numbers like an AI detection===
    # fmt: off
    detections = {
        "car": secrets.choice(detection_options),
        "person": secrets.choice(detection_options),
        "cat": secrets.choice(detection_options),
        "dog": secrets.choice(detection_options)
    }
    # fmt: on

    return detections


def send_detections():
    global message_number

    logger.info("")
    logger.info("send_detections: Starting")

    detections = detect()

    message_number = message_number + 1

    message = json.dumps({
        "message_number": message_number,
        "host": hostname,
        "at": get_ms_time(),
        "detections": {
            "car": detections["car"],
            "person": detections["person"],
            "cat": detections["cat"],
            "dog": detections["dog"]
        }
    })
    logger.info(message)

    rabbit_channel.basic_publish(exchange=app.config['MQ_EXCHANGE'], routing_key='', body=message.encode("utf8"))

    sleep_for = secrets.choice(list(range(0, 3)))
    logger.info("send_detections: Sleeping for '%s'", sleep_for)
    sleep(sleep_for)
    logger.info("send_detections: Complete")

    logger.info("")


scheduler.add_job(send_detections, 'interval', seconds=1, max_instances=1)
flask_scheduler.start()

if __name__ == '__main__':
    app.run(debug=is_run_debug, host=run_host, port=run_port)
