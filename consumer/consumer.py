#!/usr/bin/env python

import os
import json
from datetime import datetime
import time

import pika


def get_env_var(var_name):
    return os.environ[var_name]

def callback(ch, method, properties, body):
    weather_reading = json.loads(body)
    print(weather_reading)
    ch.basic_ack(delivery_tag=method.delivery_tag)

# https://pika.readthedocs.io/en/stable/examples/blocking_consume_recover_multiple_hosts.html

rabbit_host = get_env_var('RABBIT_HOST')
rabbit_username = get_env_var('RABBIT_USERNAME')
rabbit_password = get_env_var('RABBIT_PASSWORD')

while True:
    try:
        credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
        parameters = pika.ConnectionParameters(rabbit_host, 5672, '/', credentials)
        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()
        channel.queue_declare(queue='sensor_queue', durable=True)  # Avoid losing messages during crashes
        channel.basic_qos(prefetch_count=1)  # Do not give more than one message to a worker at a time
        channel.basic_consume(queue='sensor_queue', on_message_callback=callback)

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            connection.close()
            break
    except pika.exceptions.ConnectionClosedByBroker:
        # Uncomment this to make the example not attempt recovery
        # from server-initiated connection closure, including
        # when the node is stopped cleanly
        #
        # break
        time.sleep(5)
        continue
        # Do not recover on channel errors
    except pika.exceptions.AMQPChannelError as ex:
        print("Caught a channel error: {}, stopping.".format(ex))
        break
        # Recover on all other connection errors
    except pika.exceptions.AMQPConnectionError:
        print("Connection was closed, retrying.")
        time.sleep(5)
