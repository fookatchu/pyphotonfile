meta:
  id: photon
  file-extension: photon
  endian: le
  title: AnyCubic Photon mSLA layer archive (v2)
doc: |
  photon is a fileformat used by the Anycubic Photon 3D-Printer. Besides print
  properties it contains layers of images which get exposed at different layer
  heights. The images are RLE encoded. The decoding if not part of this
  definition.
  v2 of the format introduced additional print properties and the abbility to
  use anti-aliased layers. These layers are appended in different levels after
  the non-anti-aliased layers.
  Note: This is a work in progress and has not been verified.

doc-ref: |
  * definition of v1 format from https://github.com/Photonsters/PhotonFileEditor/blob/master/PhotonFile.py
  * definition of v2 format from https://github.com/Photonsters/CBDDLPinfo/blob/master/CBDDLPinfo.cs

seq:
  - id: magic
    contents: [0x19, 0x00, 0xfd, 0x12]
    doc: magic code for photon file.
  - id: version
    type: s4
    doc: specifies file version. 1 is without anti-aliasing support and 2 with anti-aliasing support and additional print properties.
  - id: bed_x
    type: f4
    doc: max print volume in mm in x direction.
  - id: bed_y
    type: f4
    doc: max print volume in mm in y direction.
  - id: bed_z
    type: f4
    doc: max print volume in mm in z direction.
  - size: 12
    doc: unused.
  - id: layer_height
    type: f4
    doc: global layer height in mm. note that the layers themself have layer heights which seem to be ignored.
  - id: exposure_time
    type: f4
    doc: exposure time of all non-bottom layers.
  - id: exposure_time_bottom
    type: f4
    doc: exposure time of bottom layers.
  - id: off_time
    type: f4
    doc: TODO.
  - id: bottom_layers
    type: s4
    doc: number of layers starting from the first that get treated as bottom layers with different exposure.
  - id: resolution_x
    type: s4
    doc: x resolution of the display.
  - id: resolution_y
    type: s4
    doc: y resolution of the display.
  - id: preview_highres
    type: preview_image
    doc: high resolution preview image which gets shown on the printers display.
  - id: ofs_layers
    type: s4
    doc: offset address of the layer definitions.
  - id: num_layers
    type: s4
    doc: number of layers in the file
  - id: preview_lowres
    type: preview_image
    doc: low resolution preview image which gets shown on the printers display.
  - id: print_time
    type: s4
    if: version > 1
    doc: estimated print time in seconds. new in version 2.
  - id: projection_type
    type: s4
    doc: TODO.
  - id: print_properties
    type: print_properties
    if: version > 1
    doc: print properties. new in version 2.
  - id: antialiasing_level
    type: s4
    doc: anti-aliasing level. 1 equals to no aa. new in version 2.
  - id: light_pwm
    type: s2
    if: version > 1
    doc: possibly light intensity of non-bottom-layers. new in version 2, unverified.
  - id: light_pwm_bottom
    type: s2
    if: version > 1
    doc: possibly light intensity of bottom-layers. new in version 2, unverified.

instances:
  layers:
    io: _root._io
    pos: ofs_layers
    type: layer
    repeat: expr
    repeat-expr: num_layers * antialiasing_level
    doc: number of layers equals to num_layers attribute multiplied by the antialiasing_level.

types:
  preview_image:
    seq:
      - id: ofs
        type: s4
        doc: address of preview image header
    instances:
      header:
        io: _root._io
        pos: ofs
        type: preview_image_header
      image:
        io: _root._io
        pos: header.ofs_image
        size: header.len_image
        doc: preview image data. imagetype unknown. TODO.

  preview_image_header:
    seq:
      - id: resolution_x
        type: s4
        doc: x resolution of the image.
      - id: resolution_y
        type: s4
        doc: y resolution of the image.
      - id: ofs_image
        type: s4
        doc: address of the image.
      - id: len_image
        type: s4
        doc: length of the image.

  print_properties:
    seq:
      - id: ofs
        type: s4
        doc: address of the print properties.
      - id: len
        type: s4
        doc: length of the print properties.
    instances:
      data:
        io: _root._io
        pos: ofs
        size: len
        type: print_properties_data


  print_properties_data:
    seq:
      - id: bottom_lift_distance
        type: f4
      - id: bottom_lift_speed
        type: f4
      - id: lifting_distance
        type: f4
      - id: lifting_speed
        type: f4
      - id: retract_speed
        type: f4
      - id: volume_ml
        type: f4
      - id: weight_g
        type: f4
      - id: cost_dollars
        type: f4
      - id: bottom_light_off_delay
        type: f4
      - id: light_off_delay
        type: f4
      - id: bottom_layer_count
        type: s4
      - id: p1
        type: f4
      - id: p2
        type: f4
      - id: p3
        type: f4
      - id: p4
        type: f4
    doc: needs verification. TODO.

  layer:
    seq:
      - id: height
        type: f4
        doc: height of the layer measurement in mm from the buildplate.
      - id: exposure
        type: f4
        doc: exposure time of the layer.
      - id: off_time
        type: f4
        doc: offtime after layer exposure.
      - id: ofs_image
        type: s4
        doc: address of the image data.
      - id: len_image
        type: s4
        doc: length of the image data.
      - size: 16
        doc: unused.
    instances:
      image:
        io: _root._io
        pos: ofs_image
        size: len_image