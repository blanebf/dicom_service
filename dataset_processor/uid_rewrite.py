# Copyright (c) 2017 Pavel 'Blane' Tuchin
from dicom.UID import generate_uid
from .processor_base import ProcessorBase


class UIDRewriter(ProcessorBase):
    def __init__(self, params=None, keep_original=False, output_dir=None):
        ProcessorBase.__init__(self, params, keep_original, output_dir)
        self.prefix = params['prefix']

    def process(self, ds):
        ds.StudyInstanceUID = generate_uid(self.prefix)
        ds.SeriesInstanceUID = generate_uid(self.prefix)
        ds.SOPInstanceUID = generate_uid(self.prefix)
        return ds
