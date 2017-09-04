# Copyright (c) 2017 Pavel 'Blane' Tuchin
from dicom.charset import python_encoding
from dicom.valuerep import text_VRs
from .processor_base import ProcessorBase


class ReEncoder(ProcessorBase):
    def __init__(self, params, keep_original=False, output_dir=None):
        ProcessorBase.__init__(self, params, keep_original, output_dir)

        self.source = params['source']
        if self.source in python_encoding:
            # Source encoding is a valid DICOM SpecificCharacterSet
            self.source = python_encoding[self.source]

        self.target = params['target']
        if self.target in python_encoding:
            # Target encoding is a valid DICOM SpecificCharacterSet
            self.target = python_encoding[self.target]

    def process(self, ds):
        self._change_charset(ds)
        if self.target in python_encoding:
            # Set SpecificCharacterSet in processed dataset if target is
            # valid DICOM encoding
            ds.SpecificCharacterSet = self.target
        else:
            for k, v in python_encoding.items():
                # If we target was specified as python encoding, than we
                # search for it in mapping and set proper SpecificCharacterSet
                # If it's not found, than SpecificCharacter set is left as-is.
                if v == self.target:
                    ds.SpecificCharacterSet = k
        return ds

    def _change_charset(self, ds):
        for element in ds:
            if element.VR in text_VRs or element.VR == 'PN':
                # We have a text element
                try:
                    if element.VM > 1:
                        element.value = [
                            e.decode(self.source).encode(self.target)
                            for e in element.value
                        ]
                    else:
                        element.value = element.decode(self.source)\
                            .encode(self.target)
                except ValueError:
                    # Leave failed elements as is.
                    pass
            elif element.VR == 'SQ':
                # We have a sequence. Call _change_charset recursively
                for item in element.value:
                    self._change_charset(item)
