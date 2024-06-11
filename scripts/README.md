

# Shared YAML formats

## Shape definitions

Some declarations like rule areas and graphics may define shapes directly, often
for manually adding items to individually-generated footprints.

These are handled in a unified way (internally, these use the `shape_properties` module)

### Rectangles

Rectangles can be defined by centre and size:

~~~yaml
- rect:
  center: [0, 0]
  size: [2, 1]
~~~

They can also be defined by the corners:

~~~yaml
- shape: rect
  corners: [
    [0, 0], # corner 1
    [1, 1]  # corner 2
  ]
~~~

## Rule areas

Can be used to specify rule areas for the footprint. The dictionary contains an entry for each area.
The following fields are supported:

- `name`: the name of the rule area in the footprint
- `layers`: a string containing the layers of the rule area, or a list of layers
- `shapes`: a list of shapes. Each shape is a dict with a single key, which is the shape type. The value is a list of
  coordinates. See the [Shape definitions](#shape-definitions) section for a list of the supported shapes.
- `keepouts`: a dict of keepout rules. One or more of `tracks`, `vias`, `copperpour`, `pads`, `footprints`.
  Each one can be `deny` or `allow` (default: `allow`).

You can inherit a rule area and redefine parts of it.

~~~yaml
rule_areas:
  key1: # key is unique for each rule area, isn't used in the final output
    name: 'Front keepout' # visible name of the rule area
    layers: 'F.Cu'  # layers of the rule area
    shapes:
      - shape: rect
        corners: [
          [0, 0], # corner 1
          [1, 1]  # corner 2
        ]
    keepouts:
      vias: deny
  key2:
    # copy key1 area, but redefine layer and keepouts
    inherit: key1
    name: 'Back keepout'
    layers: 'B.Cu'  # layers of the rule area
    keepouts:
      vias: allow
      copperpour: deny
~~~