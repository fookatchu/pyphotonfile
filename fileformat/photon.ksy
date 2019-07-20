meta:
  id: photon
  file-extension: photon
  endian: le
  title: AnyCubic Photon mSLA layer archive
seq:
  - id: magic
    type: u8
    doc: possibly magic. otherwise not used
  - id: bed_x
    type: f4
  - id: bed_y
    type: f4
  - id: bed_z
    type: f4
  - id: padding_1
    size: 12
  - id: layer_height
    type: f4
  - id: exposure_time
    type: f4
  - id: exposure_time_bottom
    type: f4
  - id: off_time
    type: f4
  - id: bottom_layers
    type: s4
  - id: resolution_x
    type: s4
  - id: resolution_y
    type: s4
  - id: preview_highres
    type: preview_image
  - id: layer_def_address
    type: s4
  - id: n_layers
    type: s4
  - id: preview_lowres
    type: preview_image
  - id: padding_2
    size: 4
  - id: projection_type
    type: s4
  - id: padding_3
    size: 24

instances:
  layers:
    io: _root._io
    pos: layer_def_address
    type: layer
    repeat: expr
    repeat-expr: n_layers

types:
  preview_image:
    seq:
      - id: header_address
        type: s4
    instances:
      header:
        io: _root._io
        pos: header_address
        type: preview_image_header
      image:
        io: _root._io
        pos: header.data_address
        size: header.data_length

  preview_image_header:
    seq:
      - id: resolution_x
        type: s4
      - id: resolution_y
        type: s4
      - id: data_address
        type: s4
      - id: data_length
        type: s4

  layer:
    seq:
      - id: height
        type: f4
      - id: exposure
        type: f4
      - id: off_time
        type: f4
      - id: data_address
        type: s4
      - id: data_length
        type: s4
      - id: padding
        size: 16
    instances:
      image:
        io: _root._io
        pos: data_address
        size: data_length