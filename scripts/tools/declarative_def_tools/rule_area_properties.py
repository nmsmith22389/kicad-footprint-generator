from dataclasses import dataclass

from . import utils, shape_properties

@dataclass
class KeepoutProperties():

    DENY = True
    ALLOW = False

    # Store the rules as booleans, the "allow"/"not_allowed" syntax
    # is only a s-expr format detail that might change in the future
    tracks: bool
    vias: bool
    copperpour: bool
    pads: bool
    footprints: bool

    def __init__(self, keepout_spec):
        self.tracks = self._get_keepout('tracks', keepout_spec)
        self.vias = self._get_keepout('vias', keepout_spec)
        self.copperpour = self._get_keepout('copperpour', keepout_spec)
        self.pads = self._get_keepout('pads', keepout_spec)
        self.footprints = self._get_keepout('footprints', keepout_spec)

    def _get_keepout(self, keepout_name, keepout_spec):
        """
        Get the value of a keepout rule. The default is to allow everything.
        """
        value = keepout_spec.get(keepout_name, 'allow')

        if value not in ['allow', 'deny']:
            raise ValueError(f"Rule {keepout_name} must be either 'allow' or 'deny'")

        return self.DENY if value == 'deny' else self.ALLOW

@dataclass
class RuleAreaProperties():
    """
    The properties for a single keepout definition, as defined in the YAML file.

    One of these definitions defines one or more physical keepout areas.
    """
    name: str
    layers: list

    # A list of rules that define the keepout area)
    keepouts: dict

    # A list of the shapes that define the keepout area(s)
    shapes: list

    def __init__(self, rule_area_spec):
        self.name = self._get_rule_area_name(rule_area_spec)
        self.layers = self._get_rule_area_layers(rule_area_spec)
        self.keepouts = KeepoutProperties(rule_area_spec.get('keepouts', {}))
        self.shapes = self._get_rule_area_shapes(rule_area_spec)

        print(self.keepouts)

    def _get_rule_area_name(self, rule_area_spec):
        """
        Get the name of the keepout area.

        This is the name of the keepout area as defined in the YAML file.

        It is allowed to have multiple keepout areas with the same name,
        and also keepout areas with no name at all: they're just strings.
        """
        return rule_area_spec.get('name', None)

    def _get_rule_area_layers(self, rule_area_spec):

        layers = rule_area_spec.get('layers', [])

        if not layers:
            raise ValueError('Must specify at least one layer for keepout area')

        return utils.as_list(layers)

    def _get_rule_area_shapes(self, rule_area_spec):
        """
        Get the shapes that define the keepout area.
        """
        shapes_spec = rule_area_spec.get('shapes', [])

        if not shapes_spec:
            raise ValueError('Must specify at least one shape for keepout area')

        shapes = []

        for shape_spec in shapes_spec:
            shape = shape_properties.construct_shape(shape_spec)
            shapes.append(shape)

        return shapes