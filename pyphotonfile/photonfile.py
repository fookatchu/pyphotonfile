import struct
import sys
import os
import numpy as np
from PIL import Image
import pkgutil
import io
import glob

# from IPython import embed

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
    Represents a layer with one (no anti-aliasing) or more SubLayers (anti-aliasing) in the Photon-file.
    """
    def __init__(self):
        self.sublayers = []

    def append_sublayer(self, sublayer):
        self.sublayers.append(sublayer)

    def __eq__(self, other):
        if not isinstance(other, Layer):
            # don't attempt to compare against unrelated types
            return NotImplemented

        if len(self.sublayers) != len(other.sublayers):
            return False

        comparisons = []
        for a, b in zip(self.sublayers, other.sublayers):
            comparisons.append(a == b)
        return all(comparisons)

    # def __repr__(self):
    #     return 'Layer(%r, %r, %r)' % (self.layer_thickness, self.exposure_time, self.off_time)

class SubLayer:
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
        if not isinstance(other, SubLayer):
            # don't attempt to compare against unrelated types
            return NotImplemented

        comparisons = []
        comparisons.append(round(self.layer_thickness, 4) == round(other.layer_thickness, 4))
        comparisons.append(round(self.exposure_time, 4) == round(other.exposure_time, 4))
        comparisons.append(round(self.off_time, 4) == round(other.off_time, 4))
        comparisons.append(self._data == other._data)
        return all(comparisons)

    def __repr__(self):
        return 'SubLayer(%r, %r, %r)' % (self.layer_thickness, self.exposure_time, self.off_time)


class Photon:
    """
    Represents a Photon-file.
    """
    def __init__(self, filepath=None):
        if filepath is None:
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
        f = io.BytesIO(data)
        self.header = f.read(4)
        self.version = struct.unpack('i', f.read(4))[0]
        self.bed_x = struct.unpack('f', f.read(4))[0]
        self.bed_y = struct.unpack('f', f.read(4))[0]
        self.bed_z = struct.unpack('f', f.read(4))[0]
        f.seek(3*4, os.SEEK_CUR)    # padding
        self.layer_height = struct.unpack('f', f.read(4))[0]
        self.exposure_time = struct.unpack('f', f.read(4))[0]
        self.exposure_time_bottom = struct.unpack('f', f.read(4))[0]
        self.off_time = struct.unpack('f', f.read(4))[0]
        self.bottom_layers = struct.unpack('i', f.read(4))[0]
        self.resolution_x = struct.unpack('i', f.read(4))[0]
        self.resolution_y = struct.unpack('i', f.read(4))[0]
        self.preview_highres_header_address = struct.unpack('i', f.read(4))[0]
        self.layer_def_address = struct.unpack('i', f.read(4))[0]
        self.n_layers = struct.unpack('i', f.read(4))[0]
        self.preview_lowres_header_address = struct.unpack('i', f.read(4))[0]
        if self.version > 1:
            self.print_time = struct.unpack('i', f.read(4))[0]
        else:
            f.seek(4, os.SEEK_CUR)    # padding
        self.projection_type = struct.unpack('i', f.read(4))[0]
        self.layer_levels = 1
        if self.version > 1:
            self.print_properties_address = struct.unpack('i', f.read(4))[0]
            self.print_properties_length = struct.unpack('i', f.read(4))[0]
            self.anti_aliasing_level = struct.unpack('i', f.read(4))[0]
            self.layer_levels = self.anti_aliasing_level
            self.light_pwm = struct.unpack('h', f.read(2))[0]
            self.light_pwm_bottom = struct.unpack('h', f.read(2))[0]

        f.seek(self.preview_highres_header_address, os.SEEK_SET)
        self.preview_highres_resolution_x = struct.unpack('i', f.read(4))[0]
        self.preview_highres_resolution_y = struct.unpack('i', f.read(4))[0]
        self.preview_highres_data_address = struct.unpack('i', f.read(4))[0]
        self.preview_highres_data_length = struct.unpack('i', f.read(4))[0]

        f.seek(self.preview_highres_data_address, os.SEEK_SET)
        self.preview_highres_data = f.read(self.preview_highres_data_length)

        f.seek(self.preview_lowres_header_address, os.SEEK_SET)
        self.preview_lowres_resolution_x = struct.unpack('i', f.read(4))[0]
        self.preview_lowres_resolution_y = struct.unpack('i', f.read(4))[0]
        self.preview_lowres_data_address = struct.unpack('i', f.read(4))[0]
        self.preview_lowres_data_length = struct.unpack('i', f.read(4))[0]

        f.seek(self.preview_lowres_data_address, os.SEEK_SET)
        self.preview_lowres_data = f.read(self.preview_lowres_data_length)

        if self.version > 1:
            f.seek(self.print_properties_address, os.SEEK_SET)
            self.bottom_lift_distance = struct.unpack('f', f.read(4))[0]
            self.bottom_lift_speed = struct.unpack('f', f.read(4))[0]
            self.lifting_distance = struct.unpack('f', f.read(4))[0]
            self.lifting_speed = struct.unpack('f', f.read(4))[0]
            self.retract_speed = struct.unpack('f', f.read(4))[0]
            self.volume_ml = struct.unpack('f', f.read(4))[0]
            self.weight_g = struct.unpack('f', f.read(4))[0]
            self.cost_dollars = struct.unpack('f', f.read(4))[0]
            self.bottom_light_off_delay = struct.unpack('f', f.read(4))[0]
            self.light_off_delay = struct.unpack('f', f.read(4))[0]
            self.bottom_layer_count = struct.unpack('i', f.read(4))[0]
            self.p1 = struct.unpack('f', f.read(4))[0]
            self.p2 = struct.unpack('f', f.read(4))[0]
            self.p3 = struct.unpack('f', f.read(4))[0]
            self.p4 = struct.unpack('f', f.read(4))[0]

        f.seek(self.layer_def_address, os.SEEK_SET)
        self.layers = []
        sublayers = []
        for level in range(self.layer_levels):
            sublayers.append([])
            for i in range(self.n_layers):
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
                sublayers[-1].append(SubLayer(data, layer_thickness, exposure_time, off_time))
                f.seek(curpos, os.SEEK_SET)
            del previous_layer_height   # dirty hack to rest thickness calculation for multiple levels / anti aliasing. does anyone actually need the thickness?
        f.close()
        for i in range(self.n_layers):  # create layer objects with sorted sublayers for easier manipulation. could be done more elegantly.
            layer = Layer()
            for level in range(self.layer_levels):
                layer.append_sublayer(sublayers[level][i])
            self.layers.append(layer)


    def write(self, filepath):
        """
        Writes the Photon-file to disk.
        """
        offsets = {}
        addresses = {}

        with open(filepath, 'wb') as f:
            f.write(self.header)
            f.write(struct.pack('i', self.version))
            f.write(struct.pack('f', self.bed_x))
            f.write(struct.pack('f', self.bed_y))
            f.write(struct.pack('f', self.bed_z))
            f.write(b'\x00' * 3 * 4)  # padding
            f.write(struct.pack('f', self.layer_height))
            f.write(struct.pack('f', self.exposure_time))
            f.write(struct.pack('f', self.exposure_time_bottom))
            f.write(struct.pack('f', self.off_time))
            f.write(struct.pack('i', self.bottom_layers))
            f.write(struct.pack('i', self.resolution_x))
            f.write(struct.pack('i', self.resolution_y))
            f.write(struct.pack('i', self.preview_highres_header_address))
            offsets['layer_def_address'] = f.tell()     # remember position in file to later add the correct address
            f.write(struct.pack('i', 0x0 ))
            f.write(struct.pack('i', len(self.layers)))
            offsets['preview_lowres_header_address'] = f.tell() # remember position in file to later add the correct address
            f.write(struct.pack('i', 0x0 ))

            if self.version > 1:
                f.write(struct.pack('i', self.print_time))
            else:
                f.write(b'\x00' * 4)  # padding
            f.write(struct.pack('i', self.projection_type))
            if self.version > 1:
                offsets['print_properties_address'] = f.tell()  # remember position in file to later add the correct address
                f.write(struct.pack('i', 0x0))
                f.write(struct.pack('i', self.print_properties_length))
                f.write(struct.pack('i', self.anti_aliasing_level))
                f.write(struct.pack('h', self.light_pwm))
                f.write(struct.pack('h', self.light_pwm_bottom))
                f.write(b'\x00' * 3 * 4)
            else:
                f.write(b'\x00' * 6 * 4)  # padding
            f.write(struct.pack('i', self.preview_highres_resolution_x))
            f.write(struct.pack('i', self.preview_highres_resolution_y))
            f.write(struct.pack('i', self.preview_highres_data_address))
            f.write(struct.pack('i', self.preview_highres_data_length))
            f.write(b'\x00' * 4 * 4)
            f.write(self.preview_highres_data)
            addresses['preview_lowres_header_address'] = f.tell()   # remember position in file to later add the correct address
            f.write(struct.pack('i', self.preview_lowres_resolution_x))
            f.write(struct.pack('i', self.preview_lowres_resolution_y))
            f.write(struct.pack('i', self.preview_lowres_data_address))
            f.write(struct.pack('i', self.preview_lowres_data_length))
            f.write(b'\x00' * 4 * 4)
            f.write(self.preview_lowres_data)
            if self.version > 1:
                addresses['print_properties_address'] = f.tell()    # remember position in file to later add the correct address
                f.write(struct.pack('f', self.bottom_lift_distance))
                f.write(struct.pack('f', self.bottom_lift_speed))
                f.write(struct.pack('f', self.lifting_distance))
                f.write(struct.pack('f', self.lifting_speed))
                f.write(struct.pack('f', self.retract_speed))
                f.write(struct.pack('f', self.volume_ml))
                f.write(struct.pack('f', self.weight_g))
                f.write(struct.pack('f', self.cost_dollars))
                f.write(struct.pack('f', self.bottom_light_off_delay))
                f.write(struct.pack('f', self.light_off_delay))
                f.write(struct.pack('i', self.bottom_layer_count))
                f.write(struct.pack('f', self.p1))
                f.write(struct.pack('f', self.p2))
                f.write(struct.pack('f', self.p3))
                f.write(struct.pack('f', self.p4))

            addresses['layer_def_address'] = f.tell()   # remember position in file to later add the correct address

            layer_data_pos = f.tell() + len(self.layers) * self.layer_levels * (9 * 4)
            layer_data_offsets = {}
            layer_data_addresses = {}
            for i, level in enumerate(range(self.layer_levels)):    # layers in header are sorted: Layer 1 Sublayer 1, L2 S1, L3 S1, ... L1 S4, L2 S4
                layer_data_offsets[i] = {}
                for j, layer in enumerate(self.layers):
                    layer = layer.sublayers[level]
                    try:
                        f.write(struct.pack('f', layer.layer_thickness + previous_layer_height))
                        previous_layer_height += layer.layer_thickness
                    except UnboundLocalError:
                        f.write(struct.pack('f', 0.0))
                        previous_layer_height = 0
                    f.write(struct.pack('f', layer.exposure_time))
                    f.write(struct.pack('f', layer.off_time))
                    layer_data_offsets[i][j] = f.tell() # remember position in file to later add the correct address
                    f.write(struct.pack('i', 0x0))
                    f.write(struct.pack('i', len(layer._data)))
                    f.write(b'\x00' * 4 * 4)
                del previous_layer_height   # dirty hack to rest thickness calculation for multiple levels / anti aliasing. does anyone actually need the thickness?
            for j, layer in enumerate(self.layers):  # layers in data are sorted: Layer 1 Sublayer 1, L1 S2, L1 S3, ... LX S1, LX S2. Different than in the header!
                for i, sublayer in enumerate(layer.sublayers):
                    try:
                        layer_data_addresses[i][j] = f.tell()
                    except KeyError:
                        layer_data_addresses[i] = {}
                        layer_data_addresses[i][j] = f.tell()
                    f.write(sublayer._data)

            # update addresses
            # header
            for key, value in offsets.items():
                f.seek(value)
                f.write(struct.pack('i', addresses[key]))
            # layers
            for level, value in layer_data_offsets.items():
                for layer, address in layer_data_addresses[level].items():
                    f.seek(layer_data_offsets[level][layer])
                    f.write(struct.pack('i', layer_data_addresses[level][layer]))

    def export_images(self, dirpath):
        """
        Exports all containing layer images to a supplied directory.
        """
        try:
            os.makedirs(dirpath)
        except OSError:
            pass
        for i, layer in enumerate(self.layers):
            for j, sublayer in enumerate(layer.sublayers):
                self.export_image(sublayer, os.path.join(dirpath, '{:05d}_{:02d}.png'.format(i, j)))

    def export_image(self, sublayer, filepath):
        """
        Exports layer image at idx to the supplied filename.
        """
        img = rle_to_imgarray(sublayer._data) * 255
        Image.fromarray(img).convert('RGB').save(filepath)


    def create_layer(self, images, layer_thickness=None, exposure_time=None, off_time=None):
        if not isinstance(images, list):
            images = [images]
        if len(images) != self.layer_levels:
            raise ValueError('supplied number of images must equal to number of levels in file')
        layer = Layer()
        for image in images:
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
            layer.append_sublayer(SubLayer(data, layer_thickness, exposure_time, off_time))
            return layer

    def append_layer(self, images, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Appends a new layer. In case of multiple levels, the correct number of images must be supplied as a list. images should be a path or already rle encoded bytes object. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        layer = self.create_layer(images, layer_thickness, exposure_time, off_time)
        self.layers.append(layer)

    def append_layers(self, dirpath, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Appends multiple new layers. dirpath should be an existing directory. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        files = glob.glob(os.path.join(dirpath, "[0-9][0-9][0-9][0-9][0-9]_[0-9][0-9].png"))
        layers = []
        last_file_id = ''
        for filepath in files:
            file_id = os.path.basename(filepath)[:5]
            if file_id == last_file_id:
                layers[-1].append(filepath)
            else:
                layers.append([filepath])
                last_file_id = file_id
        for layer in layers:
            self.append_layer(layer, layer_thickness, exposure_time, off_time)

    def insert_layer(self, images, idx, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Insert a new layer at idx. Not tested. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        layer = self.create_layer(images, layer_thickness, exposure_time, off_time)
        self.layers.insert(idx, layer)

    def replace_layer(self, images, idx, layer_thickness=None, exposure_time=None, off_time=None):
        """
        Replaces a layer a layer at idx with a nw layer. Not tested. Argument exposure_time
        seems to be not used by the firmware. If keyword args are ommited, falls back to global values.
        """
        layer = self.create_layer(images, layer_thickness, exposure_time, off_time)
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
        note that exposure time seems to be ignored on a per layer basis. If keyword args are ommited, falls
        back to global values.
        """
        for layer in self.layers:
            for sublayer in layer.sublayers:
                if layer_thickness:
                    sublayer.layer_thickness = layer_thickness
                if exposure_time:
                    sublayer.exposure_time = exposure_time
                if off_time:
                    sublayer.off_time = off_time

