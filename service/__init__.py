from collections import namedtuple
import logging
from database.models import init_sqlite
from dataset_processor.tag_morpher import TagMorpher
from directory_uploader import sender
from directory_uploader import watcher

Config = namedtuple('Config', ['senders', 'watchers', 'database', 'logging'])
Watcher = namedtuple('Watcher', ['directory', 'remove_on_send', 'send_delay',
                                 'sender'])
Sender = namedtuple('Sender', ['name', 'local_ae', 'remote_ae', 'address',
                               'port', 'processors'])

Processor = namedtuple('Processor', ['type', 'keep_original', 'output_dir',
                                     'config'])


processor_types = {
    'TagMorpher': TagMorpher
}


class Service(object):
    def __init__(self, config):
        self._setup_logging(config.logging)
        self._setup_database(config.database)
        self.senders = {k: v for k, v in self._setup_senders(config.senders)}
        self.watchers = list(self._setup_watchers(config.watchers))

    def start(self):
        for s in self.senders.values():
            s.start()
        for w in self.watchers:
            w.start()

    def stop(self):
        for w in self.watchers:
            w.stop()
        for s in self.senders.values():
            s.stop()
            s.join()

    @staticmethod
    def _setup_database(config):
        db_type = config['type']
        if db_type.lower() == 'sqlite':
            filename = config['file']
            init_sqlite(filename)
        else:
            raise Exception('Failed to initialize database')

    @staticmethod
    def _setup_logging(config):
        enable_logging = bool(config['enableLogging'])
        del config['enableLogging']
        if enable_logging:
            logging.basicConfig(**config)

    def _setup_watchers(self, watchers):
        for w in watchers:
            sender_obj = self.senders[w.sender]
            watcher_obj = watcher.Watcher(sender_obj, w.directory,
                                          w.remove_on_send, w.send_delay)
            yield watcher_obj

    @staticmethod
    def _setup_senders(senders):
        for s in senders:
            sender_obj = sender.Sender(s.local_ae, s.remote_ae, s.address, s.port)
            for proc in s.processors:
                factory = processor_types[proc.type]
                processor = factory(proc.config, proc.keep_original,
                                    proc.output_dir)
                sender_obj.add_processor(processor)
            yield s.name, sender
