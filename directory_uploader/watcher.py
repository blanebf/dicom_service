from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timedelta


class Watcher(FileSystemEventHandler):
    def __init__(self, sender, directory, remove_on_send, send_delay):
        self.sender = sender
        self.directory = directory
        self.remove_on_send = remove_on_send
        self.send_delay = send_delay

        self.observer = Observer()
        self.observer.schedule(self, path=self.directory)

    def on_created(self, event):
        if event.is_directory:
            # we don't care about directories (at least not in this version)
            return
        event_time = datetime.utcnow()
        ready_time = event_time + timedelta(seconds=self.send_delay)
        self.sender.send(event.src_path, ready_time, self.remove_on_send)

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
