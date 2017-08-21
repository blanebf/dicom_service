# Copyright (c) 2017 Pavel 'Blane' Tuchin
import argparse
import time
import sys
sys.path.append('..')

from service import Service
from config_reader import ini_reader


def main():
    parser = argparse.ArgumentParser(description='DICOM service')
    parser.add_argument('--config', help='Configuration file')
    args = parser.parse_args()
    config = ini_reader.read_config(args.config)
    service = Service(config)
    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    service.stop()

if __name__ == '__main__':
    main()
