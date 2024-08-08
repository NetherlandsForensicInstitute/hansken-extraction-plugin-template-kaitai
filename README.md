# Hansken Kaitai Plugin Template for Python

This repository contains a template for a Hansken Kaitai plugin written in Python. [Kaitai](https://kaitai.io/) enables to read binary data structures from all sorts of files or network streams.
The Kaitai plugin for Hansken, enables to parse a file using a Kaitai struct and write the parse result as a JSON. The template contains the general structure of a Kaitai plugin, including the required build steps.

- To get started developing Hansken Extraction Plugins, read the [Getting Started Documentation](https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/python/getting_started.html).
- It is strongly recommended to take note of the [Hansken Extraction Plugins for plugin developers documentation](https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/).
- For more information on the supported formats by Kaitai, go to https://formats.kaitai.io/. 
- An example implementation of a Hansken Kaitai plugin is found [here](https://github.com/NetherlandsForensicInstitute/hansken-extraction-plugin-sdk-examples/tree/main/python/appledoublekaitai).

To transform this template into an implementation, we suggest to conduct the following steps:
* Clone the template plugin to get started on implementing your Kaitai plugin for Hansken
* Go to [`https:/ide.kaitai.io/`](Kaitai) to download a Kaitai token. This is the ```.ksy``` file you need in the next step.
* Place the *.ksy file of interest in the [`structs`](structs) directory
* Update the plugin info in [`plugin.py`](plugin.py)
* Make sure you set the matcher on the FireFli filetype of your interest in [`plugin.py`](plugin.py) with a suitable HQL statement
* Create test input data in the folder [`testdata/input`](testdata/input)
  (refer to the SDK manual for more details on how to define test data)
* Add additional dependencies for your plugin to [`requirements.in`](requirements.in) if necessary 
* If you added additional dependencies, regenerate `requirements.txt` by calling `tox -e upgrade`
* Add any system dependencies to the [`Dockerfile`](Dockerfile)
* (Re)generate your expected test result data with `tox -e regenerate`
* Verify your expected test result data in [`testdata/result`](testdata/result)
* Update this `README.md`
* Publish your plugin to the Hansken community

Tox commands that may be useful:
* `tox`: runs your tests
* `tox -e integration-test`: runs your tests against the packaged version of your plugin (requires Docker)
* `tox -e regenerate`: regenerates the expected test results (use after you update your plugin)
* `tox -e upgrade`: regenerates `requirements.txt` from [`requirements.in`](requirements.in)
* `tox -e package`: creates a extraction plugin OCI/Docker image that can be published to Hansken (requires Docker)

Note: see the readme text in the [`Dockerfile`](Dockerfile) if you need to set proxies or private Python package registries for building a plugin.

