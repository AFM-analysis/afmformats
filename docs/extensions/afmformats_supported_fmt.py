"""supported file formats by afmformats

Usage
-----
Directives:

List of supported file formats

   .. afmformats_file_formats::

"""
from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from sphinx.util.nodes import nested_parse_with_titles
from docutils import nodes

import afmformats


class Base(Directive):
    required_arguments = 0
    optional_arguments = 0

    def generate_rst(self):
        pass

    def run(self):
        rst = self.generate_rst()

        vl = ViewList(rst, "fakefile.rst")
        # Create a node.
        node = nodes.section()
        node.document = self.state.document
        # Parse the rst.
        nested_parse_with_titles(self.state, vl, node)
        return node.children


class Formats(Base):
    def generate_rst(self):
        rst = []

        rst.append("")
        rst.append(".. csv-table::")
        rst.append("    :header: Format introduced by, Description, "
                   + "Extension, Loader")
        rst.append("    :widths: 15, 5, 20, 60")
        rst.append("    :delim: tab")
        rst.append("")

        # generate a new dict with maker-keys
        loader_dict = {}
        for recipe in afmformats.formats.formats_available:
            # group by loader
            k = recipe["loader"].__name__ + recipe["descr"] + recipe["suffix"]
            loader_dict[k] = {
                "ext": recipe["suffix"],
                "mod": ":func:`{}.{}`".format(
                    recipe["loader"].__module__.split(".", 1)[1],
                    recipe["loader"].__name__),
                "mak": recipe["maker"],
                "des": recipe["descr"]
                }
        for item in sorted(loader_dict.values(), key=lambda x: x["ext"]):
            rst.append("    {}\t {}\t {} \t {}".format(
                item["mak"], item["des"], item["ext"], item["mod"]))

        rst.append("")

        return rst


def setup(app):
    app.add_directive('afmformats_file_formats', Formats)
    return {'version': '0.2'}   # identifies the version of our extension
