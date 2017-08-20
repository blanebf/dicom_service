import os
import dicom


class TagMorpher(object):
    def __init__(self, attribute_map, keep_original=False, output_dir=None):
        self.keep_original = keep_original
        if self.keep_original and not output_dir:
            raise ValueError('Output directory should be specified for '
                             'keeping original file')
        self.output_dir = output_dir
        self.attribute_map = attribute_map

    def process_file(self, filename):
        fn = os.path.basename(filename)
        ds = dicom.read_file(filename)
        for attr, value in self.attribute_map.items():
            setattr(ds, attr, value)
        if self.keep_original:
            filename = os.path.join(self.output_dir, fn)

        ds.save_as(filename)
        return filename
