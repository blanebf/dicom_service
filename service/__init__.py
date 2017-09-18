from collections import namedtuple
import logging
import threading
from database.models import init_sqlite
from dataset_processor.tag_morpher import TagMorpher
from dataset_processor.uid_rewrite import UIDRewriter
from dataset_processor.reencoder import ReEncoder
from directory_uploader import sender
from directory_uploader import watcher
from . import dicom_srv

Config = namedtuple('Config', ['senders', 'watchers', 'database', 'logging',
                               'dicom_service'])
Watcher = namedtuple('Watcher', ['directory', 'remove_on_send', 'send_delay',
                                 'senders', 'recursive'])
Sender = namedtuple('Sender', ['name', 'local_ae', 'remote_ae', 'address',
                               'port', 'processors'])

Processor = namedtuple('Processor', ['type', 'keep_original', 'output_dir',
                                     'config'])
DICOMService = namedtuple('DICOMService', ['storage_dir', 'ae_title', 'port',
                                           'move_handlers', 'find_handlers',
                                           'store_handlers', 'devices'])
DICOMHandler = namedtuple('DICOMHandler', ['type', 'config'])
DICOMDevice = namedtuple('DICOMDevice', ['name', 'ae_title', 'address', 'port'])


processor_types = {
    'TagMorpher': TagMorpher,
    'UIDWriter': UIDRewriter,
    'ReEncoder': ReEncoder
}


class Service(object):
    def __init__(self, config):
        self._setup_logging(config.logging)
        self._setup_database(config.database)
        self.senders = {k: v for k, v in self._setup_senders(config.senders)}
        self.watchers = list(self._setup_watchers(config.watchers))
        self.dicom_service = self._setup_dicom_service(config.dicom_service)

    def start(self):
        if self.dicom_service:
            threading.Thread(target=self.dicom_service.serve_forever).start()
        for s in self.senders.values():
            s.start()
        for w in self.watchers:
            w.start()

    def stop(self):
        if self.dicom_service:
            self.dicom_service.quit()
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
        if 'level' in config:
            # convert logging level to string
            config['level'] = int(config['level'])
        del config['enableLogging']
        if enable_logging:
            logging.basicConfig(**config)

    def _setup_watchers(self, watchers):
        for w in watchers:
            senders = [self.senders[s] for s in w.senders]
            watcher_obj = watcher.Watcher(senders, w.directory,
                                          w.remove_on_send, w.send_delay,
                                          w.recursive)
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
            yield s.name, sender_obj

    def _setup_dicom_service(self, dicom_conf):
        if not dicom_conf:
            return None
        service = dicom_srv.DICOMService(dicom_conf.storage_dir,
                                         dicom_conf.ae_title,
                                         dicom_conf.port)
        for handler in dicom_conf.find_handlers:
            find_handler = dicom_srv.HANDLERS[handler.type](self,
                                                            handler.config)
            service.add_find(find_handler)
        for handler in dicom_conf.store_handlers:
            store_handler = dicom_srv.HANDLERS[handler.type](self,
                                                             handler.config)
            service.add_storage(store_handler)
        return service
