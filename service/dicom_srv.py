# Copyright (c) 2017 Pavel 'Blane' Tuchin

from itertools import chain
import logging

from dicom.UID import UID, ImplicitVRLittleEndian, ExplicitVRBigEndian, \
    ExplicitVRLittleEndian, DeflatedExplicitVRLittleEndian

from netdicom2 import StorageAE
from netdicom2.sopclass import SUCCESS

from dicom_handlers import storage_service

logger = logging.getLogger(__name__)

SUPPORTED_TS = [
    ImplicitVRLittleEndian,
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ExplicitVRBigEndian,
    DeflatedExplicitVRLittleEndian,
    # 'JPEG Baseline (Process 1)
    UID('1.2.840.10008.1.2.4.50'),
    #: JPEG Extended (Process 2 and 4)
    UID('1.2.840.10008.1.2.4.51'),
    # JPEG Lossless, Non-Hierarchical (Process 14)
    UID('1.2.840.10008.1.2.4.57'),
    # JPEG Lossless, Non-Hierarchical, First-Order Prediction
    # (Process 14 [Selection Value 1])
    UID('1.2.840.10008.1.2.4.70'),
    #: JPEG-LS Lossless Image Compression
    UID('1.2.840.10008.1.2.4.80'),
    # JPEG-LS Lossy (Near-Lossless) Image Compression'
    UID('1.2.840.10008.1.2.4.81'),
    # JPEG 2000 Image Compression (Lossless Only)
    UID('1.2.840.10008.1.2.4.90'),
    # JPEG 2000 Image Compression
    UID('1.2.840.10008.1.2.4.91'),
    # JPEG 2000 Part 2 Multi-component Image Compression (Lossless Only)
    UID('1.2.840.10008.1.2.4.92'),
    # JPEG 2000 Part 2 Multi-component Image Compression
    UID('1.2.840.10008.1.2.4.93'),
    # JPIP Referenced
    UID('1.2.840.10008.1.2.4.94'),
    # JPIP Referenced Deflate'
    UID('1.2.840.10008.1.2.4.95'),
    # MPEG2 Main Profile @ Main Level
    UID('1.2.840.10008.1.2.4.100'),
    # MPEG2 Main Profile @ High Level
    UID('1.2.840.10008.1.2.4.101'),
    # MPEG-4 AVC/H.264 High Profile / Level 4.1
    UID('1.2.840.10008.1.2.4.102'),
    # MPEG-4 AVC/H.264 BD-compatible High Profile / Level 4.1
    UID('1.2.840.10008.1.2.4.103'),
    # RLE Lossless
    UID('1.2.840.10008.1.2.5'),
    # RFC 2557 MIME encapsulation
    UID('1.2.840.10008.1.2.6.1'),
    # XML Encoding
    UID('1.2.840.10008.1.2.6.2'),
]


HANDLERS = {}


def add_handler(handler):
    HANDLERS[handler.name] = handler


add_handler(storage_service.LoggingStorage)
add_handler(storage_service.Forwarding)


class DICOMService(StorageAE):
    def __init__(self, storage_dir, ae_title, port,
                 max_pdu_length=65536):
        StorageAE.__init__(self, storage_dir, ae_title, port, SUPPORTED_TS,
                           max_pdu_length)
        self.storage_handlers = []
        self.find_handlers = []

    def add_storage(self, store_handler):
        for service in store_handler.services:
            self.add_scp(service)
        self.storage_handlers.append(store_handler)

    def add_find(self, find_handler):
        for service in find_handler.services:
            self.add_scp(service)
        self.find_handlers.append(find_handler)

    def on_receive_store(self, context, ds):
        statuses = [h(context, ds) for h in self.storage_handlers]
        # Sorted statuses and return status with the highest code (error)
        sorted(statuses, cmp=lambda a: a.code_range[0])
        return statuses[-1]

    def on_receive_find(self, context, ds):
        responses = (h(context, ds) for h in self.find_handlers)
        for ds, status in chain(responses):
            if status != SUCCESS:
                yield None, status
                break
            yield ds, status
        else:
            yield None, SUCCESS
