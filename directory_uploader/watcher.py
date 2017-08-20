# Copyright (c) 2017 Pavel 'Blane' Tuchin

import logging
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


logger = logging.getLogger(__name__)


class Watcher(FileSystemEventHandler):
    def __init__(self, sender, directory, remove_on_send, send_delay):
        self.sender = sender
        self.directory = directory
        self.remove_on_send = remove_on_send
        self.send_delay = send_delay

        self.logger = logger.getChild('Watcher')

        self.observer = Observer()
        self.observer.schedule(self, path=self.directory)

    def on_created(self, event):
        if event.is_directory:
            # we don't care about directories (at least not in this version)
            return
        self.logger.info('New file in directory %s: %s', self.directory,
                         event.src_path)
        event_time = datetime.utcnow()
        ready_time = event_time + timedelta(seconds=self.send_delay)
        try:
            self.sender.send(event.src_path, ready_time, self.remove_on_send)
        except Exception:
            self.logger.exception('Failed to send file %s', event.src_path)

    def start(self):
        self.logger.info('Starting watcher on directory %s', self.directory)
        self.observer.start()

    def stop(self):
        self.logger.info('Stopping watcher on directory %s', self.directory)
        self.observer.stop()
        self.observer.join()
        self.logger.info('Stopped watcher on directory %s', self.directory)
