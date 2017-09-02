# Copyright (c) 2017 Pavel 'Blane' Tuchin
from .processor_base import ProcessorBase


class TagMorpher(ProcessorBase):
    def __init__(self, attribute_map, keep_original=False, output_dir=None):
        ProcessorBase.__init__(self, attribute_map, keep_original, output_dir)
        self.attribute_map = attribute_map

    def process(self, ds):
        for attr, value in self.attribute_map.items():
            setattr(ds, attr, value)
        return ds
