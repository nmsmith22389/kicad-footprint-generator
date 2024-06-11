from typing import List

# Common key for generic additional tags
ADDITIONAL_TAGS_KEY = 'additional_tags'


class TagsProperties:
    """
    Class that reads "additional tags" out of standard
    YAML spec files.

    This is currently very simple, as tags are just arrays of strings.
    """
    _tags: List[str]

    def __init__(self, tags: List[str]):
        self._tags = tags

    @property
    def tags(self):
        return self._tags
