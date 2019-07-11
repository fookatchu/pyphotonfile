meta:
  id: photon
  file-extension: photon
  endian: le
  title: AnyCubic Photon mSLA layer archive (v2)
seq:
  - id: magic
    contents: [0x19, 0x00, 0xfd, 0x12]
  - id: version
    type: s4
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
  - id: print_time
    type: s4
    if: version > 1
  - id: projection_type
    type: s4
  - id: print_properties
    type: print_properties
    if: version > 1
  - id: antialiasing_level
    type: s4
    # if: version > 1
  - id: light_pwm
    type: s2
    if: version > 1
  - id: light_pwm_bottom
    type: s2
    if: version > 1

instances:
  layers:
    io: _root._io
    pos: layer_def_address
    type: layer
    repeat: expr
    repeat-expr: n_layers * antialiasing_level

types:
  preview_image:
    seq:
      - id: address
        type: s4
    instances:
      header:
        io: _root._io
        pos: address
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

  print_properties:
    seq:
      - id: address
        type: s4
      - id: length
        type: s4
    instances:
      data:
        io: _root._io
        pos: address
        size: length
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