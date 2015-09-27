# -*- coding: iso-8859-1 -*-
"""
YAML configuration file loading routines.
"""
import yaml
import os
import codecs

# Force UTF-8 encoding for all Yaml files.
YamlEncoding = 'utf-8'

class Loader(yaml.SafeLoader):
    """Loader with file inclusion support.
       a: !include b.yaml
    """

    def __init__(self, stream):
        """Initialize root name."""
        if hasattr(stream, 'name'):
            self._root = os.path.split(stream.name)[0]
        else:
            self._root = ""
        super(Loader, self).__init__(stream)

    def include(self, node):
        """Include a file."""
        filename = os.path.join(self._root, self.construct_scalar(node))
        with codecs.open(filename, 'r', YamlEncoding) as f:
            return yaml.load(f, Loader)

Loader.add_constructor('!include', Loader.include)


def load_stream(stream):
    """Load options from a YAML stream."""
    return yaml.load(stream, Loader)


def load_file(filename):
    """Load options from a YAML file."""
    if os.path.isfile(filename):
        with codecs.open(filename, 'r', YamlEncoding) as f:
            return load_stream(f)
    return {}


def write_file(filename, content):
    """Write options to a YAML file."""
    with codecs.open(filename, 'w', YamlEncoding) as f:
        yaml.dump(content, f)
