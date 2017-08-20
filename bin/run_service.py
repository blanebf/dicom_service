# Copyright (c) 2017 Pavel 'Blane' Tuchin
import argparse
import ConfigParser
import logging
import time
import sys
sys.path.append('..')

from directory_uploader import setup_watchers, Sender, Watcher
from database.models import init_sqlite


def main():
    parser = argparse.ArgumentParser(description='DICOM service')
    parser.add_argument('--config', help='Configuration file')
    args = parser.parse_args()
    config = ConfigParser.ConfigParser()
    with open(args.config) as fp:
        config.readfp(fp)
    enable_logging = config.getboolean('logging', 'enableLogging')
    if enable_logging:
        _format = config.get('logging', 'format')
        log_level = config.getint(20)
        filename = config.get('logging', 'filename')
        logging.basicConfig(format=_format, level=log_level,
                            filename=filename)
    db_type = config.get('database', 'type')
    if db_type.lower() == 'sqlite':
        filename = config.get('databse', 'file')
        init_sqlite(filename)
    else:
        raise Exception('Failed to initialize databse')
    senders = read_senders(config)
    watchers = read_watchers(config)
    service = setup_watchers(senders, watchers)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    service.stop()


def read_senders(config):
    result = []
    count = config.getint('senders', 'count')
    if not count:
        return result
    for i in range(count):
        section = 'sender{}'.format(i)
        name = config.get(section, 'name')
        local_ae = config.get(section, 'local_ae')
        remote_ae = config.get(section, 'remote_ae')
        address = config.get(section, 'address')
        port = config.getint(section, 'port')
        sender = Sender(name=name, local_ae=local_ae, remote_ae=remote_ae,
                        address=address, port=port)
        result.append(sender)
    return result


def read_watchers(config):
    result = []
    count = config.getint('watchers', 'count')
    if not count:
        return result
    for i in range(count):
        section = 'watcher{}'.format(i)
        directory = config.get(section, 'directory')
        remove_on_send = config.getboolean(section, 'remove_on_send')
        send_delay = config.getint(section, 'send_delay')
        sender = config.get(section, 'sender')
        watcher = Watcher(directory=directory, remove_on_send=remove_on_send,
                          send_delay=send_delay, sender=sender)
        result.append(watcher)
    return result


if __name__ == '__main__':
    main()
