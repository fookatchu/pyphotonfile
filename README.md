pyPhotonfile is a library used for manipulating Photon- and cbddlp-files created for the Anycubic Photon 3D-Printer and compatibles (e.g. Elegoo Mars, etc.). Currently it supports removing and adding new layers as well as changing global parameters like the exposure time, etc. You are free to play around with all exposed variables, but be aware that changes might not be supported by the printer firmwares. Let me know if you crash your printer so that I can implement safety measures. 
A general description of the fileformat can be found in folder 'fileformat' including fancy graphs.
It is based on the work done by [PhotonFileEditor](https://github.com/Photonsters/PhotonFileEditor). While PhotonFileEditor works, I was in need of a clean library which is why I refactored most of the code.
pyPhotonfile is the backbone of [SL1toPhoton](https://github.com/fookatchu/SL1toPhoton).

Friendly Reminder
=================
   Use at your own risk. Please verify that what you are doing will not break your printer. A good test is to load the resulting files into ChituBox to see if everything is at its right place.

Installation
=================
```
pip install pyphotonfile
```
or for the bleeding edge version from the master repo:
```
pip install git+https://github.com/fookatchu/pyphotonfile@master
```

Example Usage
========================================
```python
from pyphotonfile import Photon

in_filepath = "input.photon"   # .photon or compatible cbddlp-file
out_filepath = "output.photon"

# export images
photon = Photon(in_filepath)
photon.export_images("tempdir")

# import images
photon.delete_layers()  # we want to clear the layers first
photon.append_layers("tempdir") # reimport previously exported images. the files need to have the same filenaming scheme
photon.write(out_filepath)

# info
print(photon.layers)    # list containing all layers with sublayers
print(photon.layers[0].sublayers[0])  # first sublayer of the first layer. anti-aliasing files contian multiple sublayers, otherwise their is only one sublayer
print(photon.layers[0].sublayers[0].layer_thickness)    # layers have individual properties which might not be recognized by the firmware. feel free to play around
print(photon.layers[0].sublayers[0].exposure_time)
print(photon.layers[0].sublayers[0].off_time)

# modification of global parameters
photon.exposure_time = 10
photon.bottom_layers = 3

# the shown variables below are the only meaningfull ones. Be aware that these are not protected. change those values at your own risk!
print(photon.header)
print(photon.version)
print(photon.bed_x)
print(photon.bed_y)
print(photon.bed_z)
print(photon.layer_height)
print(photon.exposure_time)
print(photon.exposure_time_bottom)
print(photon.off_time)
print(photon.bottom_layers)
print(photon.resolution_x)
print(photon.resolution_y)
print(photon.n_layers)
print(photon.projection_type)
print(photon.preview_highres_resolution_x)
print(photon.preview_highres_resolution_y)
print(photon.preview_lowres_resolution_x)
print(photon.preview_lowres_resolution_y)
print(len(photon.preview_highres_data)) # don't print the raw data. the preview images are not yet parsed. interested in implementing something?
print(len(photon.preview_lowres_data)) # don't print the raw data. the preview images are not yet parsed. interested in implementing something?

if photon.version > 1:
    print(photon.anti_aliasing_level)
    print(photon.layer_levels)
    print(photon.light_pwm)
    print(photon.light_pwm_bottom)
    print(photon.print_time)
    print(photon.bottom_lift_distance)
    print(photon.bottom_lift_speed)
    print(photon.lifting_distance)
    print(photon.lifting_speed)
    print(photon.retract_speed)
    print(photon.volume_ml)
    print(photon.weight_g)
    print(photon.cost_dollars)
    print(photon.bottom_light_off_delay)
    print(photon.light_off_delay)
    print(photon.bottom_layer_count)
    print(photon.p1)
    print(photon.p2)
    print(photon.p3)
    print(photon.p4)
```

TODO / Roadmap (contributions welcome)
========================================
 - add support for anti-aliasing feature / 'v2' photon-file format
 - release proper documentation
 - remove dependency of template binary file for newly created photon-files
 - add support for photonS file format
