import pytest
import os
import glob
import pyphotonfile
from pyphotonfile import photonfile


def test_photonfile_no_modifications(temp_folder):
    photon = photonfile.Photon('tests\\testfiles\\pyphotonfile_reference.photon')
    photon.write(os.path.join(temp_folder + 'pyphotonfile_reference.photon'))

    with open(os.path.join(temp_folder + 'pyphotonfile_reference.photon'), 'rb') as f:
        new_crc = f.read()
    with open('tests\\testfiles\\pyphotonfile_reference.photon', 'rb') as f:
        old_crc = f.read()
    assert old_crc == new_crc


def test_photonfile_properties(temp_folder):
    photon_original = photonfile.Photon('tests\\testfiles\\pyphotonfile_reference.photon')
    # photon_original.write(os.path.join(temp_folder + 'pyphotonfile_reference.photon'))
    photon_new = photonfile.Photon('tests\\testfiles\\pyphotonfile_reference.photon')
    photon_new.export_images(temp_folder)
    photon_new.delete_layers()
    paths = []
    for filepath in glob.glob(os.path.join(temp_folder, '*.png')):
        paths.append(filepath)
        photon_new.append_layer(paths[-1])
    photon_new.write(os.path.join(temp_folder + 'pyphotonfile_reference.photon'))
    photon_new = photonfile.Photon(os.path.join(temp_folder + 'pyphotonfile_reference.photon'))
    parameters_valid = []
    for layer_new, layer_old in zip(photon_new.layers, photon_original.layers):
        parameters_valid.append(layer_new == layer_old)

    parameters_valid.append(photon_new._header == photon_original._header)
    parameters_valid.append(photon_new._bed_x == photon_original._bed_x)
    parameters_valid.append(photon_new._bed_y == photon_original._bed_y)
    parameters_valid.append(photon_new._bed_z == photon_original._bed_z)
    parameters_valid.append(photon_new.layer_height == photon_original.layer_height)
    parameters_valid.append(photon_new.exposure_time == photon_original.exposure_time)
    parameters_valid.append(photon_new.exposure_time_bottom == photon_original.exposure_time_bottom)
    parameters_valid.append(photon_new.off_time == photon_original.off_time)
    parameters_valid.append(photon_new.bottom_layers == photon_original.bottom_layers)
    parameters_valid.append(photon_new._resolution_x == photon_original._resolution_x)
    parameters_valid.append(photon_new._resolution_y == photon_original._resolution_y)
    parameters_valid.append(photon_new._preview_highres_header_address == photon_original._preview_highres_header_address)
    parameters_valid.append(photon_new._layer_def_address == photon_original._layer_def_address)
    parameters_valid.append(len(photon_new.layers) == len(photon_original.layers))
    parameters_valid.append(photon_new._preview_lowres_header_address == photon_original._preview_lowres_header_address)
    parameters_valid.append(photon_new._projection_type == photon_original._projection_type)
    parameters_valid.append(photon_new._preview_highres_resolution_x == photon_original._preview_highres_resolution_x)
    parameters_valid.append(photon_new._preview_highres_resolution_y == photon_original._preview_highres_resolution_y)
    parameters_valid.append(photon_new._preview_highres_data_address == photon_original._preview_highres_data_address)
    parameters_valid.append(photon_new._preview_highres_data_length == photon_original._preview_highres_data_length)
    assert True == all(parameters_valid)  # yes, im a bad boy.

def test_insert_layer():
    raise NotImplementedError

def test_replace_layer():
    raise NotImplementedError

def test_delete_layer():
    raise NotImplementedError