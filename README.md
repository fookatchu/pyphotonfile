pyPhotonfile is a library used for manipulating Photon-files created for the Anycubic Photon 3D-Printer. Currently it supports removing and adding new layers as well as changing global parameters like the exposure time, etc.
A general description of the fileformat can be found in folder 'fileformat' including fancy graphs.
It is based on the work done by [PhotonFileEditor](https://github.com/Photonsters/PhotonFileEditor). While PhotonFileEditor works, I was in need of a clean library which is why I refactored most of the code.
pyPhotonfile is the backbone of [SL1toPhoton](https://github.com/fookatchu/SL1toPhoton).

Friendly Reminder
=================
   Use at your own risk. Please verify that what you are doing will not break your printer.

Installation
=================
```
pip install pyphotonfile
```

Example Usage
========================================
```python
    from pyphotonfile import Photon

    photon = Photon('in_file.Photon')
    for layer in photon.layers:
        print(layer)
    photon.export_images('tempdir')
    photon.delete_layers()
    for filepath in os.listdir('tempdir'):
        photon.append_layer(filepath)
    photon.exposure_time = 10
    photon.bottom_layers = 3
    photon.write('out_file.Photon')
```

TODO / Roadmap (contributions welcome)
========================================
 - add support for anti-aliasing feature / 'v2' photon-file format
 - release proper documentation
 - remove dependency of template binary file for newly created photon-files
 - add support for photonS file format
