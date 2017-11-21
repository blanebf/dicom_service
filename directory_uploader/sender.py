# Copyright (c) 2017 Pavel 'Blane' Tuchin
import os
import time
from datetime import datetime
import logging
from threading import Thread
from peewee import TextField, DateTimeField, BooleanField, CharField, \
    IntegerField, DatabaseError
import dicom
from dicom.errors import InvalidDicomError
from netdicom2.applicationentity import ClientAE
from netdicom2.sopclass import storage_scu
from database.models import BaseModel, database_proxy


logger = logging.getLogger(__name__)


class OutgoingQueue(BaseModel):
    local_ae = CharField(max_length=16, index=True)
    remote_ae = CharField(max_length=16, index=True)
    address = CharField(max_length=255)
    port = IntegerField()
    filename = TextField()
    send_ready = DateTimeField(index=True)
    remove_on_send = BooleanField()
    is_sent = BooleanField(default=False)


class Sender(Thread):
    def __init__(self, local_ae, remote_ae, address, port):
        Thread.__init__(self)
        self.logger = logger.getChild('Sender.{}'.format(remote_ae))
        self.local_ae = local_ae
        self.remote_ae = remote_ae
        self.address = address
        self.port = port
        self.is_stopped = False
        self.processors = []
        if not OutgoingQueue.table_exists():
            # create table queue only if it doesn't exists
            with database_proxy.transaction('immediate'):
                OutgoingQueue.create_table()

    def send(self, filename, send_time, remove_on_send):
        try:
            dicom.read_file(filename, stop_before_pixels=True)
        except InvalidDicomError:
            self.logger.info('Skip not DICOM file %s', filename)
            return

        with database_proxy.transaction('immediate'):
            self.logger.info('Adding new file to the queue %s', filename)
            OutgoingQueue.create(
                filename=filename,
                send_ready=send_time,
                local_ae=self.local_ae,
                remote_ae=self.remote_ae,
                address=self.address,
                port=self.port,
                remove_on_send=remove_on_send
            )

    def add_processor(self, processor):
        self.processors.append(processor)

    def run(self):
        while not self.is_stopped:
            self.process_queue()
            time.sleep(0.5)

    def stop(self):
        self.is_stopped = True

    def process_queue(self):
        with database_proxy.execution_context(with_transaction=False):
            now = datetime.utcnow()
            try:
                query = OutgoingQueue.select().where(
                    OutgoingQueue.send_ready < now,
                    OutgoingQueue.local_ae == self.local_ae,
                    OutgoingQueue.remote_ae == self.remote_ae,
                    OutgoingQueue.is_sent == False
                ).limit(1)
            except DatabaseError:
                self.logger.exception('Query failed')
                return

            for record in query:
                filename = record.filename
                try:
                    self.logger.info('Sending file %s', filename)
                    self.send_file(record)
                except Exception as e:
                    self.logger.exception('Failed to send file %s',
                                          filename)
                else:
                    record.is_sent = True
                    with database_proxy.transaction('immediate'):
                        record.save()

                try:
                    awaiting = OutgoingQueue.select().where(
                        OutgoingQueue.local_ae != self.local_ae,
                        OutgoingQueue.filename == filename,
                        OutgoingQueue.is_sent == False
                    )
                except DatabaseError:
                    self.logger.exception('Query failed')
                    return

                if not awaiting and os.path.exists(filename):
                    os.remove(filename)

    def send_file(self, record):
        ds = dicom.read_file(record.filename, stop_before_pixels=True)
        sop_class = ds.file_meta.MediaStorageSOPClassUID
        ts = ds.file_meta.TransferSyntaxUID
        ae = ClientAE(self.local_ae, supported_ts=[ts]).add_scu(storage_scu)
        remote_ae = dict(
            aet=self.remote_ae,
            address=self.address,
            port=self.port
        )
        filename = record.filename
        for processor in self.processors:
            filename = processor.process_file(filename)

        with ae.request_association(remote_ae) as asce:
            srv = asce.get_scu(sop_class)
            srv(filename, 1)
