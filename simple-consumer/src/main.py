from os import getenv
import logging

from dotenv import load_dotenv
from os.path import realpath, dirname
import pika


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    root_dir = realpath(dirname(realpath(__file__)) + "/..")
    load_dotenv(dotenv_path=f"{root_dir}/.env")
    logging.basicConfig(level=getenv("LOGLEVEL", "INFO").upper())

    mq_url = getenv("AMPQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F?connection_attempts=3&heartbeat=3600")
    mq_exchange = getenv("AMPQ_EXCHANGE", "exchange")
    mq_exchange_type = getenv("AMPQ_EXCHANGE_TYPE", "fanout")
    mq_topic = getenv("AMPQ_TOPIC", "detected")

    params = pika.URLParameters(mq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=mq_exchange, exchange_type=mq_exchange_type)

    result = channel.queue_declare(queue='simple-consumer', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=mq_exchange, queue=queue_name)

    logger.info(' [*] Waiting for logs. To exit press CTRL+C')


    def callback(ch, method, properties, body):
        logger.info(" [x] %r" % body)


    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
