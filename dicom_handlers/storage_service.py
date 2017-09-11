# Copyright (c) 2017 Pavel 'Blane' Tuchin
import logging
import dicom
from netdicom2.sopclass import SUCCESS, storage_scp


logger = logging.getLogger(__name__)


class LoggingStorage(object):
    name = 'LoggingStorage'
    services = [storage_scp]

    def __init__(self, config=None):
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
