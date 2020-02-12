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
        rst.append("    :header: Format introduced by, Extensions, Loaders")
        rst.append("    :widths: 30, 10, 60")
        rst.append("    :delim: tab")
        rst.append("")

        # generate a new dict with maker-keys
        maker_dict = {}
        for recipe in afmformats.formats.formats_available:
            # group by maker + loader
            maker = recipe["maker"] + recipe["loader"].__name__
            if maker not in maker_dict:
                maker_dict[maker] = {"ext": [],
                                     "mod": [],
                                     "mak": []}
            maker_dict[maker]["ext"].append(recipe["suffix"])
            maker_dict[maker]["mak"].append(recipe["maker"])
            mod = ":func:`{}.{}`".format(recipe["loader"].__module__,
                                         recipe["loader"].__name__)
            maker_dict[maker]["mod"].append(mod)

        for item in sorted(maker_dict.values(), key=lambda x: x["ext"]):
            rst.append("    {}\t {}\t {}".format(
                item["mak"][0],
                ", ".join(sorted(set(item["ext"]))),
                ", ".join(sorted(set(item["mod"])))
            ))

        rst.append("")

        return rst


def setup(app):
    app.add_directive('afmformats_file_formats', Formats)
    return {'version': '0.2'}   # identifies the version of our extension
