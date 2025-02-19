from KicadModTree.nodes import Node


class EmbeddedFonts(Node):
    '''
    Class that represents an embedded_font node in a Kicad footprint

    For the time being there is no embedded font support in KiCad generated footprints,
    but if it were added, it would go here.

    We still use this node, because the format expects one (since v9) and omitting
    it causes diffs when saved in KiCad.
    '''

    def __init__(self):
        super().__init__()

    @property
    def enabled(self):
        return False
