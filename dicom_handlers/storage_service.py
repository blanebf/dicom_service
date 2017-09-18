# Copyright (c) 2017 Pavel 'Blane' Tuchin
from datetime import datetime
import logging
import dicom
from netdicom2.sopclass import SUCCESS, WARNING, storage_scp


logger = logging.getLogger(__name__)


class LoggingStorage(object):
    name = 'LoggingStorage'
    services = [storage_scp]

    def __init__(self, _, config=None):
        self.logger = logger.getChild('LoggingStorage')
        self.logger.info('Got config {}'.format(config))

    def __call__(self, context, ds):
        """Simple dicom_handlers handler that only dumps received dataset to log

        :param context: presentation context
        :param ds: dataset file object
        :return: handler always return success error code
        """
        logger.info('Received file with context %s', repr(context))
        ds = dicom.read_file(ds)
        logger.info('Dumping received dataset')
        logger.info('{}'.format(ds))
        return SUCCESS


class Forwarding(object):
    name = 'Forwarding'
    services = [storage_scp]

    def __init__(self, parent, config):
        self.logger = logger.getChild('Forwarding')
        self.logger.info('Starting forwarding with config: {}'.format(config))
        self.senders = config['senders'].split(',')
        self.remove_on_send = config.get('remove_on_send', False)
        self.parent = parent

    def __call__(self, context, ds):
        logger.info('Handling file with context %s', repr(context))
        # TODO: Add some more reliable way of getting file name.
        filename = ds.name
        result = SUCCESS
        for name in self.senders:
            sender = self.parent.seners[name]
            if sender.is_stopped:
                continue
            try:
                sender.send(filename, datetime.utcnow(), self.remove_on_send)
            except Exception:
                self.logger.exception('Failed to send file %s', filename)
                result = WARNING
        return result
