import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


class MyYAML(YAML):
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()

    def load_file(self, filename: Path):
        with filename.open("r") as f:
            return self.load(f)

    def save_file(self, filename: Path, data: dict):
        with filename.open("w") as f:
            self.dump(data, f)


yaml = MyYAML()
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=4, offset=2)
