afmformats documentation
========================
To install the requirements for building the documentation, run

    cd docs
    pip install -r requirements.txt

To compile the documentation, run

    sphinx-build . _build

Notes
=====
To view the sphinx inventory of DryMass, run

   python -m sphinx.ext.intersphinx 'http://afmformats.readthedocs.io/en/latest/objects.inv'
