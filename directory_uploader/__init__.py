from collections import namedtuple
from . import sender
from . import watcher

Watcher = namedtuple('Watcher', ['directory', 'remove_on_send', 'send_delay',
                                 'sender'])
Sender = namedtuple('Sender', ['name', 'local_ae', 'remote_ae', 'address',
                               'port'])


class UploaderService(object):
    def __init__(self, senders, watchers):
        self.senders = senders
        self.watchers = watchers

    def stop(self):
        for w in self.watchers:
            w.stop()
        for s in self.senders:
            s.stop()
            s.join()


def setup_watchers(senders, watchers):
    senders = init_senders(senders)
    service = UploaderService(senders.values(), [])
    for w in watchers:
        sender_obj = senders[w.sender]
        watcher_obj = watcher.Watcher(sender_obj, w.directory, w.remove_on_send,
                                      w.send_delay)
        watcher_obj.start()
        service.watchers.append(watcher_obj)
    return service


def init_senders(senders):
    result = {}
    for s in senders:
        sender_obj = sender.Sender(s.local_ae, s.remote_ae, s.address, s.port)
        sender_obj.start()
        result[s.name] = sender
    return result
