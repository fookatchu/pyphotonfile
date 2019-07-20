import struct
import sys
import os
import numpy as np
from PIL import Image
import pkgutil
import io

def rle_to_imgarray(data):
    """
    Decodes a RLE byte array imgarray.
    Based and honestly mostly copied from: https://github.com/Photonsters/PhotonFileEditor
    """
    # Encoding scheme:
    #     Highest bit of each byte is color (black or white)
    #     Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
    data = np.frombuffer(data, dtype=np.uint8)

    # Extract color value (highest bit) and nr of repetitions (lowest 7 bits)
    valbin = data >> 7  # only read 1st bit
    nr = data & ~(1 << 7)  # turn highest bit of

    # Make a 2d array like [ [3,0] [2,1], [nr_i,val_i]...] using the colorvalues (val) and repetitions(nr)
    runs = np.column_stack((nr, valbin))

    # Decoding magic
    runs_t = np.transpose(runs)
    lengths = runs_t[0].astype(int)
    values = runs_t[1].astype(int)
    starts = np.concatenate(([0], np.cumsum(lengths)[:-1]))
    starts, lengths, values = map(np.asarray, (starts, lengths, values))
    ends = starts + lengths
    n = ends[-1]
    x = np.full(n, 0)
    for lo, hi, val in zip(starts, ends, values):
        x[lo:hi] = val
    rgb2d = x.reshape((2560,1440))                # data is stored in rows of 2560
    return rgb2d


def imgarr_to_rle(imgarr):
    """
    Converts image array to RLE encoded byte string.
    Based on: https://github.com/Photonsters/PhotonFileEditor
    """
    # Encoding scheme:
    #     Highest bit of each byte is color (black or white)
    #     Lowest 7 bits of each byte is repetition of that color, with max of 125 / 0x7D
    x = imgarr.flatten()
    where = np.flatnonzero
    x = np.asarray(x)
    n = len(x)
    if n == 0:      # this should not happen if the image has the correct dimensions
        return np.array([], dtype=np.int)

    starts = np.r_[0, where((x[1:] - x[:-1]).astype(bool)) + 1]  # start of color changes
    lengths = np.diff(np.r_[starts, n])     # length of color run
    colors = x[starts]  # color of each run

    repetitions = lengths // 0x7d  # length of each run. calculated with integer division
    run_ends = lengths % 0x7d  # remaining part of the run, calculated with mod
    bin_colors = (colors > 0) << 7 | 0x7d   # convert colors to binary representation
    repetitions[run_ends == 0] = repetitions[run_ends == 0] - 1   # 'fix' for 42 % 42 == 0. repetitions get used as np.insert indexes, and 0 means no insertion.
    run_ends[run_ends == 0] = 0x7D   # again 'fix' for 42 % 42 == 0.
    bin_run_ends = (colors > 0) << 7 | run_ends   # binary representation of last values in the run

    data = np.repeat(bin_colors, repetitions)     # fill array with runs
    data = np.insert(data, repetitions.cumsum(), bin_run_ends)   # insert the last elements of each run
    rle_data = data.astype('uint8').tobytes()
    return rle_data

def image_to_imgarr(filepath):
    """
    Loads an image from disk and returns a numpy array. Raises ValueError if the image does not have the correct resolution of 1440x2560.
    """
    imgarr = Image.open(filepath).convert('L')
    if not (imgarr.width, imgarr.height) == (1440, 2560):
        raise ValueError("Your image dimensions are off and should be 1440x2560")
    imgarr = np.array(imgarr)
    return imgarr

class Layer:
    """
    Represents a single layer in the Photon-file.
    """
    def __init__(self, data, layer_thickness=None, exposure_time=None, off_time=None):
        self.layer_thickness = layer_thickness
        self.exposure_time = exposure_time  # currently ignored by firmware?
        self.off_time = off_time
        self._data = data
        self._data_length = len(self._data)

    def __eq__(self, other):
        if not isinstance(other, Layer):
            # don't attempt to compare against unrelated types
            return NotImplemented

        comparisons = []
        comparisons.append(round(self.layer_thickness, 4) == round(other.layer_thickness, 4))
        comparisons.append(round(self.exposure_time, 4) == round(other.exposure_time, 4))
        comparisons.append(round(self.off_time, 4) == round(other.off_time, 4))
        comparisons.append(self._data == other._data)
        return all(comparisons)

    def __repr__(self):
        return 'Layer(%r, %r, %r)' % (self.layer_thickness, self.exposure_time, self.off_time)


class Photon:
    """
    Represents a Photon-file.
    """
    def __init__(self, filepath=None):
        if filepath is None:
            # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'tests', 'testfiles', 'newfile.photon')
            # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'newfile.photon')
            # self._open(filepath)
            self._open()
            self.delete_layers()
        else:
            self._open(filepath)

    def _open(self, filepath=None):
        if filepath is None:
            data = pkgutil.get_data(__package__, 'newfile.photon')
        else:
            with open(filepath, 'rb') as f:
                data = f.read()
        # embed()
        f = io.BytesIO(data)
        self._header = f.read(4)
        self._version = struct.unpack('i', f.read(4))[0]
        self._bed_x = struct.unpack('f', f.read(4))[0]
        self._bed_y = struct.unpack('f', f.read(4))[0]
        self._bed_z = struct.unpack('f', f.read(4))[0]
        f.seek(3*4, os.SEEK_CUR)    # padding
        self.layer_height = struct.unpack('f', f.read(4))[0]
        self.exposure_time = struct.unpack('f', f.read(4))[0]
        self.exposure_time_bottom = struct.unpack('f', f.read(4))[0]
        self.off_time = struct.unpack('f', f.read(4))[0]
        self.bottom_layers = struct.unpack('i', f.read(4))[0]
        self._resolution_x = struct.unpack('i', f.read(4))[0]
        self._resolution_y = struct.unpack('i', f.read(4))[0]
        self._preview_highres_header_address = struct.unpack('i', f.read(4))[0]
        self._layer_def_address = struct.unpack('i', f.read(4))[0]
        self.n_layers = struct.unpack('i', f.read(4))[0]
        self._preview_lowres_header_address = struct.unpack('i', f.read(4))[0]
        if self._version > 1:
            self._print_time = struct.unpack('i', f.read(4))[0]
        else:
            f.seek(4, os.SEEK_CUR)    # padding
        self._projection_type = struct.unpack('i', f.read(4))[0]
        self.layer_levels = 1
        if self._version > 1:
            self._print_properties_address = struct.unpack('i', f.read(4))[0]
            self._print_properties_length = struct.unpack('i', f.read(4))[0]
            self._anti_aliasing_level = struct.unpack('i', f.read(4))[0]
            self.layer_levels = self._anti_aliasing_level
            self.light_pwm = struct.unpack('h', f.read(2))[0]
            self.light_pwm_bottom = struct.unpack('h', f.read(2))[0]
        # else:
        #     f.seek(6*4, os.SEEK_CUR)    # padding

        f.seek(self._preview_highres_header_address, os.SEEK_SET)
        self._preview_highres_resolution_x = struct.unpack('i', f.read(4))[0]
        self._preview_highres_resolution_y = struct.unpack('i', f.read(4))[0]
        self._preview_highres_data_address = struct.unpack('i', f.read(4))[0]
        self._preview_highres_data_length = struct.unpack('i', f.read(4))[0]
        # f.seek(4*4, os.SEEK_CUR)    # padding
        self._preview_highres_data = f.read(self._preview_highres_data_length)

        f.seek(self._preview_lowres_header_address, os.SEEK_SET)
        self._preview_lowres_resolution_x = struct.unpack('i', f.read(4))[0]
        self._preview_lowres_resolution_y = struct.unpack('i', f.read(4))[0]
        self._preview_lowres_data_address = struct.unpack('i', f.read(4))[0]
        self._preview_lowres_data_length = struct.unpack('i', f.read(4))[0]
        # f.seek(4*4, os.SEEK_CUR)    # padding
        self._preview_lowres_data = f.read(self._preview_lowres_data_length)

        if self._version > 1:
            f.seek(self._print_properties_address, os.SEEK_SET)
            self._bottom_lift_distance = struct.unpack('f', f.read(4))[0]
            self._bottom_lift_speed = struct.unpack('f', f.read(4))[0]
            self._lifting_distance = struct.unpack('f', f.read(4))[0]
            self._lifting_speed = struct.unpack('f', f.read(4))[0]
            self._retract_speed = struct.unpack('f', f.read(4))[0]
            self._volume_ml = struct.unpack('f', f.read(4))[0]
            self._weight_g = struct.unpack('f', f.read(4))[0]
            self._cost_dollars = struct.unpack('f', f.read(4))[0]
            self._bottom_light_off_delay = struct.unpack('f', f.read(4))[0]
            self._light_off_delay = struct.unpack('f', f.read(4))[0]
            self._bottom_layer_count = struct.unpack('i', f.read(4))[0]
            self._p1 = struct.unpack('f', f.read(4))[0]
            self._p2 = struct.unpack('f', f.read(4))[0]
            self._p3 = struct.unpack('f', f.read(4))[0]
            self._p4 = struct.unpack('f', f.read(4))[0]

        f.seek(self._layer_def_address, os.SEEK_SET)
        self.layers = []
        for i in range(self.n_layers * self.layer_levels):
            layer_height = struct.unpack('f', f.read(4))[0]
            try:
                layer_thickness = layer_height - previous_layer_height
            except UnboundLocalError:
                layer_thickness = self.layer_height
                previous_layer_height = layer_thickness
            previous_layer_height = layer_height
            exposure_time = struct.unpack('f', f.read(4))[0]
            off_time = struct.unpack('f', f.read(4))[0]
            address = struct.unpack('i', f.read(4))[0]
            data_length = struct.unpack('i', f.read(4))[0]
            f.seek(4*4, os.SEEK_CUR)    # padding
            curpos = f.tell()
            f.seek(address, os.SEEK_SET)
            data = f.read(data_length)
            self.layers.append(Layer(data, layer_thickness, exposure_time, off_time))
            f.seek(curpos, os.SEEK_SET)
        f.close()

    def write(self, filepath):
        """
        Writes the Photon-file to disk.
        """
        self._update()
        with open(filepath, 'wb') as f:
            f.write(self._header)
            f.write(struct.pack('i', self._version))
            f.write(struct.pack('f', self._bed_x))
            f.write(struct.pack('f', self._bed_y))
            f.write(struct.pack('f', self._bed_z))
            f.write(b'\x00' * 3 * 4)  # padding
            f.write(struct.pack('f', self.layer_height))
            f.write(struct.pack('f', self.exposure_time))
            f.write(struct.pack('f', self.exposure_time_bottom))
            f.write(struct.pack('f', self.off_time))
            f.write(struct.pack('i', self.bottom_layers))
            f.write(struct.pack('i', self._resolution_x))
            f.write(struct.pack('i', self._resolution_y))
            f.write(struct.pack('i', self._preview_highres_header_address))
            # print(f.tell())
            f.write(struct.pack('i', self._layer_def_address))
            f.write(struct.pack('i', len(self.layers)))
            f.write(struct.pack('i', self._preview_lowres_header_address))
            if self._version > 1:
                f.write(struct.pack('i', self._print_time))
            else:
                f.write(b'\x00' * 4)  # padding
            f.write(struct.pack('i', self._projection_type))
            if self._version > 1:
                # self._print_properties_address = struct.unpack('i', f.read(4))[0]
                f.write(struct.pack('i', self._print_properties_address))
                # self._print_properties_length = struct.unpack('i', f.read(4))[0]
                f.write(struct.pack('i', self._print_properties_length))
                # self._anti_aliasing_level = struct.unpack('i', f.read(4))[0]
                f.write(struct.pack('i', self._anti_aliasing_level))
                # self.layer_levels = self._anti_aliasing_level
                # self.light_pwm = struct.unpack('h', f.read(2))[0]
                f.write(struct.pack('h', self.light_pwm))
                # self.light_pwm_bottom = struct.unpack('h', f.read(2))[0]
                f.write(struct.pack('h', self.light_pwm_bottom))
                f.write(b'\x00' * 2 * 4)
            else:
                f.write(b'\x00' * 6 * 4)  # padding
            # f.seek(self._preview_highres_header_address, os.SEEK_SET)
            f.write(struct.pack('i', self._preview_highres_resolution_x))
            f.write(struct.pack('i', self._preview_highres_resolution_y))
            f.write(struct.pack('i', self._preview_highres_data_address))
            f.write(struct.pack('i', self._preview_highres_data_length))
            # f.seek(4*4, os.SEEK_CUR)    # padding
            f.write(b'\x00' * 4 * 4)
            f.write(self._preview_highres_data)

            # f.seek(self._preview_lowres_header_address, os.SEEK_SET)
            f.write(struct.pack('i', self._preview_lowres_resolution_x))
            f.write(struct.pack('i', self._preview_lowres_resolution_y))
            f.write(struct.pack('i', self._preview_lowres_data_address))
            f.write(struct.pack('i', self._preview_lowres_data_length))
            # f.seek(4*4, os.SEEK_CUR)    # padding
            f.write(b'\x00' * 4 * 4)
            f.write(self._preview_lowres_data)

            layer_height = 0
            layer_data_pos = f.tell() + len(self.layers) * (9 * 4)
            layer_data_offset = 0

            for layer in self.layers:
                try:
                    f.write(struct.pack('f', layer.layer_thickness + previous_layer_height))
                    previous_layer_height += layer.layer_thickness
                except UnboundLocalError:
                    f.write(struct.pack('f', 0.0))
                    previous_layer_height = 0
                f.write(struct.pack('f', layer.exposure_time))
                f.write(struct.pack('f', layer.off_time))
                f.write(struct.pack('i', layer_data_pos + layer_data_offset))
                f.write(struct.pack('i', len(layer._data)))
                f.write(b'\x00' * 4 * 4)
                layer_height += layer.layer_thickness
                layer_data_offset += len(layer._data)
            for layer in self.layers:
                f.write(layer._data)

    def _update(self):
        """
        Updates all internal address. Should not be called directly.
        """
        self._preview_lowres_header_address = self._preview_highres_header_address + 8 * 4 + self._preview_highres_data_length
        self._layer_def_address = self._preview_lowres_header_address + 8 * 4 + self._preview_lowres_data_length
        layer_data_offset = self._layer_def_address + len(self.layers) * (9 * 4)
        self.layers[0]._address = layer_data_offset
        layer_data_offset += self.layers[0]._data_length
        for i, layer in enumerate(self.layers[1:]):
            layer._address = layer_data_offset
            layer_data_offset += layer._data_length

    def export_images(self, dirpath):
        """
        Exports all containing layer images to a supplied directory.
        """
        try:
            os.makedirs(dirpath)
        except OSError:
            pass
        for i, layer in enumerate(self.layers):
            self.export_image(i, os.path.join(dirpath, '{0:05d}.png'.format(i)))

    def export_image(self, idx, filepath):
        """
        Exports layer image at idx to the supplied filename.
        """
        img = rle_to_imgarray(self.layers[idx]._data) * 255
        Image.fromarray(img).convert('RGB').save(filepath)

    def append_layer(self, image, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Appends a new layer. image should be a path or already rle encoded bytes object. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        if not isinstance(image, bytes):
            data = imgarr_to_rle(image_to_imgarr(image))
        else:
            data = image
        if layer_thickness is None:
            layer_thickness = self.layer_height
        if exposure_time is None:
            if len(self.layers) < self.bottom_layers:
                exposure_time = self.exposure_time_bottom
            else:
                exposure_time = self.exposure_time
        if off_time is None:
            off_time = self.off_time
        layer = Layer(data, layer_thickness, exposure_time, off_time)
        self.layers.append(layer)

    def append_layers(self, dirpath, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Appends multiple new layers. dirpath should be an existing directory. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        for filepath in os.listdir(dirpath):
            self.append_layer(os.path.join(dirpath, filepath), layer_thickness, exposure_time, off_time)

    def insert_layer(self, filepath, idx, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Insert a new layer at idx. Not tested. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        data = imgarr_to_rle(image_to_imgarr(filepath))
        layer = Layer(data, layer_thickness, exposure_time, off_time)
        self.layers.insert(idx, layer)

    def replace_layer(self, filepath, idx, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Replaces a layer a layer at idx with a nw layer. Not tested. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        data = imgarr_to_rle(image_to_imgarr(filepath))
        layer = Layer(data, layer_thickness, exposure_time, off_time)
        self.delete_layer(idx)
        self.insert_layer(idx, layer)

    def delete_layer(self, idx):
        """
        Delete layer at idx.
        """
        self.layers.pop(idx)

    def delete_layers(self):
        """
        Delete all layers.
        """
        self.layers = []

    def overwrite_layer_parameters(self, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Used to overwrite all layer parameters. Usefull for quick testing of a print without resin. Please
        note taht exposure time seems to be ignored on a per layer basis. If keyword args are ommited, falls
        back to global values.
        """
        for layer in self.layers:
            if layer_thickness:
                layer.layer_thickness = layer_thickness
            if exposure_time:
                layer.exposure_time = exposure_time
            if off_time:
                layer.off_time = off_time

if __name__ == '__main__':
    import shutil
    photon = Photon(sys.argv[1])
    for layer in photon.layers:
        imgarr = rle_to_imgarray(layer._data)
        rle_heikos = imgarr_to_rle(imgarr)
    try:
        shutil.rmtree('tempdir')
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree('tempdir2')
    except FileNotFoundError:
        pass
    photon.export_images('tempdir')
    photon.delete_layers()
    paths = []
    for filepath in os.listdir('tempdir'):
        paths.append(os.path.join('tempdir', filepath))
    photon.append_layers(paths)
    photon.write('testwrite.photon')
    photon.export_images('tempdir2')