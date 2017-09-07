# Copyright (c) 2017 Pavel 'Blane' Tuchin
import ConfigParser
from service import Config, Sender, Watcher, Processor


def read_config(filenames):
    config = ConfigParser.ConfigParser()
    config.read(filenames)
    log_config = section_to_dict(config, 'logging')
    db_config = section_to_dict(config, 'database')
    senders = read_senders(config)
    watchers = read_watchers(config)
    return Config(senders=senders, watchers=watchers, database=db_config,
                  logging=log_config)


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
        processors_count = config.getint(section, 'processors')
        processors = read_processors(config, section, processors_count)
        sender = Sender(name=name, local_ae=local_ae, remote_ae=remote_ae,
                        address=address, port=port, processors=processors)
        result.append(sender)
    return result


def read_processors(config, section, count):
    result = []
    if not count:
        return result
    for i in range(count):
        proc_section = '{}.processor{}'.format(section, i)
        proc_type = config.get(proc_section, 'type')
        keep_original = config.getboolean(proc_section, 'keepOriginal')
        output_dir = config.get(proc_section, 'outputDir')
        proc_conf_section = '{}.config'.format(proc_section)
        proc_conf = {k: v for k, v in config.items(proc_conf_section)}
        processor = Processor(type=proc_type, keep_original=keep_original,
                              output_dir=output_dir, config=proc_conf)
        result.append(processor)
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
        senders = config.get(section, 'sender').split(',')
        senders = [s.trim() for s in senders]
        recursive = config.get(section, 'recursive')
        watcher = Watcher(directory=directory, remove_on_send=remove_on_send,
                          send_delay=send_delay, senders=senders,
                          recursive=recursive)
        result.append(watcher)
    return result


def section_to_dict(config, section):
    return {k: v for k, v in config.items(section)}
