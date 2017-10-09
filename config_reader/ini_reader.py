# Copyright (c) 2017 Pavel 'Blane' Tuchin
import ConfigParser
import os.path
from service import Config, Sender, Watcher, Processor, DICOMDevice, \
    DICOMHandler, DICOMService


def read_config(filenames):
    if not filenames:
        raise ValueError('No config files present')
    config = ConfigParser.RawConfigParser()
    config.optionxform = str
    config.read(filenames)
    if config.has_section('files'):
        # read other config files
        if isinstance(filenames, basestring):
            # only single file was passed to config reader
            root = os.path.dirname(filenames)
        else:
            # multiple files were passed to config reader
            # assume the first one is the main and take its directory as root
            root = os.path.dirname(filenames[0])
        extra_files = [v for _, v in config.items('files')]
        extra_files = [f if os.path.isabs(f) else os.path.join(root, f)
                       for f in extra_files]
        config.read(extra_files)
    log_config = section_to_dict(config, 'logging')
    db_config = section_to_dict(config, 'database')
    senders = read_senders(config)
    watchers = read_watchers(config)
    dicom_service = read_dicom_service(config)
    return Config(senders=senders, watchers=watchers, database=db_config,
                  logging=log_config, dicom_service=dicom_service)


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
        senders = config.get(section, 'senders').split(',')
        senders = [s.strip() for s in senders]
        recursive = config.getboolean(section, 'recursive')
        watcher = Watcher(directory=directory, remove_on_send=remove_on_send,
                          send_delay=send_delay, senders=senders,
                          recursive=recursive)
        result.append(watcher)
    return result


def read_dicom_service(config):
    if not config.has_section('dicom'):
        return None
    ae_title = config.get('dicom', 'ae_title')
    storage_dir = config.get('dicom', 'storage_dir')
    port = config.getint('dicom', 'port')
    devices = read_devices(config)
    find_handlers = read_handlers(config, 'find_handlers')
    store_handlers = read_handlers(config, 'store_handlers')
    move_handlers = read_handlers(config, 'move_handlers')
    return DICOMService(storage_dir=storage_dir, ae_title=ae_title,
                        port=port, move_handlers=move_handlers,
                        find_handlers=find_handlers,
                        store_handlers=store_handlers,
                        devices=devices)


def read_devices(config):
    result = []
    count = config.getint('devices', 'count')
    if not count:
        return result
    for i in range(count):
        section = 'device{}'.format(i)
        name = config.get(section, 'name')
        ae_title = config.get(section, 'ae_title')
        address = config.get(section, 'address')
        port = config.getint(section, 'port')
        device = DICOMDevice(name=name, ae_title=ae_title, address=address,
                             port=port)
        result.append(device)
    return result


def read_handlers(config, section):
    result = []
    count = config.getint(section, 'count')
    if not count:
        return result
    for i in range(count):
        sub_section = '{}{}'.format(section, i)
        handler_type = config.get(sub_section, 'type')
        config_section = '{}{}'.format(sub_section, 'config')
        if config.has_section(config_section):
            handler_conf = section_to_dict(config, config_section)
        else:
            handler_conf = {}
        handler = DICOMHandler(type=handler_type, config=handler_conf)
        result.append(handler)
    return result


def section_to_dict(config, section):
    return {k: v for k, v in config.items(section)}
