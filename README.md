pyPhotonfile is a library used for manipulating Photon-files created for the Anycubic Photon 3D-Printer. Currently it supports removing and adding
new layers as well as changing global parameters like the exposure time, etc.
It is based on the work done by `PhotonFileEditor`_. While PhotonFileEditor works, I was in need of a clean library which is why I refactored most of the code.

.. _PhotonFileEditor: https://github.com/Photonsters/PhotonFileEditor

.. DANGER::
   Use at your own risk. This is the first release!

Example Usage
========================================

.. code-block:: python

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
