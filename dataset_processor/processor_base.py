# Copyright (c) 2017 Pavel 'Blane' Tuchin
import os
import dicom


class ProcessorBase(object):
    def __init__(self, params, keep_original=False, output_dir=None):
        self.keep_original = keep_original
        if self.keep_original and not output_dir:
            raise ValueError('Output directory should be specified for '
                             'keeping original file')
        self.output_dir = output_dir
        self.params = params

    def process_file(self, filename):
        fn = os.path.basename(filename)
        ds = dicom.read_file(filename)
        ds = self.process(ds)
        if self.keep_original:
            filename = os.path.join(self.output_dir, fn)

        ds.save_as(filename)
        return filename

    def process(self, ds):
        raise NotImplementedError('Method should be overridden in child '
                                  'classes')