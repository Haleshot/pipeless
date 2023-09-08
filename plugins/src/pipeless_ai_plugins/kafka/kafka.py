import os
import sys
from confluent_kafka import Producer

# LE metemos self.kafka.version, self.kafka.producer y se configura solo con env vars
# How do people register plugins they do?
# How do we load people plugins?

# We cani automatically load all the plugins under the plugins directory of the running application automatically, so users simply need to clone plugins inside that directory
# Plugins should embed stuff into the self.<plugin_id> into the PipelessApp class such as version, and any fiel that they may want to expose

# Pipeless can read the plugin metadata and load the plugin class under self.<plugin-id> so that the builder of the plugin just need to export functions.
# Pipeless can execute the plugin constructor on load
# How does the plugin execute actions on every stage? Should pipeless consider that and execute each plugin stage method in order before the user code? Each plugin should have a stage method like the user app plus an init method (not the as before since before will be executed on every iteration of the worker)
# We can create the PipelessPlugin interface
# How do users download plugins? How does pipeless install plugin dependencies (the user must install dependencies manually as documented on the plugin README)?
# We can add a command to the CLI to install a plugin by its name when available on our official index or from a git repo url when not. It will simply download it to the plugins folder and it could install 
# When a plugin executes codes on the frame, it should modify the original frame so the user doesn't have to invoke anything. After the latest plugin the frame will be passed to the user code
# In this way plugins can do both things, execute code on stages as well as provide custom functions to the user

# How do we isolate the variables of each plugin? By adding the plugin id. We should check on the plugin initialization if there is already a self.plugin_id variable, which means two plugins are trying to register with the same id

class KafkaProducer:
    """
    This class allows to send the data extracted from the stream to a Kafka topic.
    """
    def __init__(self):
        """
        Creates and configures the Kafka producer

        Config env vars:
        - KAFKA_BOOTSTRAP_SERVERS: a comma separated list of host and port. Ex: 'host1:9092,host2:9092'
        - KAFKA_CLIENT_ID (optional): the client ID for the connection
        - KAFKA_USERNAME (optional): username when using SASL or SCRAM authentication
        - KAFKA_PASSWORD (optional): password when using SASL or SCRAM authentication
        """
        bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', None)
        if bootstrap_servers is None:
            print('ERROR: missing KAFKA_BOOTSTRAP_SERVERS env var')
            sys.exit(1)
        conf = { 'bootstrap.servers': bootstrap_servers }
        client_id = os.environ.get('KAFKA_CLIENT_ID', None)
        if client_id is not None:
            conf["client.id"] = client_id

        self.__producer = Producer(conf)

        username = os.environ.get('KAFKA_USERNAME', None)
        password = os.environ.get('KAFKA_PASSWORD', None)
        if username is not None and password is not None:
            self.__producer.set_sasl_credentials(username, password)
        elif username is not None:
            print('ERROR: KAFKA_USERNAME was provided but KAFKA_PASSWORD WAS NOT')
        elif password is not None:
            print('ERROR: KAFKA_PASSWORD was provided but KAFKA_USERNAME WAS NOT')

    def produce(self, topic : str, value : str | bytes, key : str | bytes = None,
        partition : int = None, on_delivery : callable = None):
        """
        Send data to a topic

        Params:
        - topic (str): name of the topic to produce the message to
        - value (str|bytes): Message payload.
        - key (srt|bytes): optional. Message key
        - partition (int): optional. Partition to produce to
        - on_delivery(err,msg)(function): optional. Callback to call after success or failed delivery
        """
        named_params = {}
        if key is not None: named_params['key'] = key
        if partition is not None: named_params['partition'] = partition
        if on_delivery is not None: named_params['on_delivery'] = on_delivery
        self.__producer.produce(topic, value, **named_params)
        self.__producer.poll(1) # TODO: check the implications of this timeout
