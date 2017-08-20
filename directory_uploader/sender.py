# Copyright (c) 2017 Pavel 'Blane' Tuchin
import os
import time
from datetime import datetime
import logging
from threading import Thread
from peewee import TextField, DateTimeField, BooleanField, CharField, \
    IntegerField, DatabaseError
import dicom
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

    def send(self, filename, send_time, remove_on_send):
        with database_proxy.atomic():
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
        with database_proxy.atomic():
            now = datetime.utcnow()
            try:
                query = OutgoingQueue.select().where(
                    OutgoingQueue.send_ready < now,
                    OutgoingQueue.local_ae == self.local_ae,
                    OutgoingQueue.remote_ae == self.remote_ae,
                    OutgoingQueue.is_sent == False
                )
            except DatabaseError:
                self.logger.exception('Query failed')
                return

            for record in query:
                try:
                    self.logger.info('Sending file %s', record.filename)
                    self.send_file(record)
                except Exception:
                    self.logger.exception('Failed to send file %s',
                                          record.filename)
                else:
                    record.is_sent = True
                    record.save()

    def send_file(self, record):
        ds = dicom.read_file(record.filename, stop_before_pixels=True)
        sop_class = ds.file_meta.MediaStorageSOPClassUID
        ts = ds.filename.TransferSyntax
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
        if record.remove_on_send:
            os.remove(filename)
