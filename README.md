# Hansken Kaitai Plugin Template for Python

This repository contains a template for a Hansken Kaitai plugin written in Python. [Kaitai](https://kaitai.io/) enables to read binary data structures from all sorts of files or network streams.
The Kaitai plugin for Hansken, enables to parse a file using a Kaitai struct and write the parse result as a JSON. The template contains the general structure of a Kaitai plugin, including the required build steps.

- To get started developing Hansken Extraction Plugins, read the [Getting Started Documentation](https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/python/getting_started.html).
- It is strongly recommended to take note of the [Hansken Extraction Plugins for plugin developers documentation](https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/).
- For more information on the supported formats by Kaitai, go to https://formats.kaitai.io/. 
- An example implementation of a Hansken Kaitai plugin is found [in the extraction plugin examples repository](https://github.com/NetherlandsForensicInstitute/hansken-extraction-plugin-sdk-examples/tree/main/python/appledoublekaitai).

To transform this template into an implementation, we suggest to conduct the following steps:
* Clone the template plugin to get started on implementing your Kaitai plugin for Hansken
* Go to the [kaitai_structs_formats Github](https://github.com/kaitai-io/kaitai_struct_formats/tree/acdf0733633568c68869af15846abaf1c0eaa59a) to download a Kaitai token. 
  This is the ```.ksy``` file you need in the next step.
* Place the *.ksy file of interest in the [`structs`](structs) directory
* Update the plugin info in [`plugin.py`](plugin.py), such as:
  * the version of your plugin, author info, and your organisation
  * the matcher on the `$data.fileType` property of your interest in [`plugin.py`](plugin.py) with a suitable HQL-Lite statement
    (see also "[how to write a good matcher](https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/concepts/hql_lite.html#how-to-write-a-matcher)" in the documentation).
* Create test input data in the folder [`testdata/input`](testdata/input)
  (refer to the["Test Framework" section](https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/concepts/test_framework.html) of the SDK manual for more details on how to define test data) 
* Add additional dependencies for your plugin to [`requirements.in`](requirements.in) if necessary 
* If you added additional dependencies, regenerate `requirements.txt` by calling `tox -e upgrade`
* Add any system dependencies to the [`Dockerfile`](Dockerfile)
* (Re)generate your expected test result data with `tox -e regenerate`
* Verify your expected test result data in [`testdata/result`](testdata/result)
* Update this `README.md`
* Publish your plugin to the Hansken community


> **TIP!**\
> If you want to run the plugin from your IDE, you can add the `.ksy` file and the manually compiled `.py` files to the [structs](./structs) folder.

> **WARNING!**\
> Successful implementations of this template have only been tested on small object trees and small byte arrays. Stability and performance for large object trees and byte arrays is not guaranteed.


Tox commands that may be useful:
* `tox`: runs your tests
* `tox -e integration-test`: runs your tests against the packaged version of your plugin (requires Docker)
* `tox -e regenerate`: regenerates the expected test results (use after you update your plugin)
* `tox -e upgrade`: regenerates `requirements.txt` from [`requirements.in`](requirements.in)
* `tox -e package`: creates a extraction plugin OCI/Docker image that can be published to Hansken (requires Docker)

Note: see the readme text in the [`Dockerfile`](Dockerfile) if you need to set proxies or private Python package registries for building a plugin.

