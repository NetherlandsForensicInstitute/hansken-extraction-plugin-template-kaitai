from hansken_extraction_plugin.api.extraction_plugin import ExtractionPlugin
from hansken_extraction_plugin.api.plugin_info import Author, MaturityLevel, PluginId, PluginInfo
from hansken_extraction_plugin.runtime.extraction_plugin_runner import run_with_hanskenpy
from logbook import Logger

import kaitai_utils


log = Logger(__name__)


class Plugin(ExtractionPlugin):

    def plugin_info(self):
        plugin_info = PluginInfo(
            id=PluginId(domain='{YOUR_ORGANISATION_DOMAIN}', category='extract', name='{FILETYPE NAME}'),
            version='1.0.0',
            description='description of your plugin',
            author=Author('Your name', 'your@email.address', 'your organisation'),
            maturity=MaturityLevel.PROOF_OF_CONCEPT,
            webpage_url='',  # e.g. url to the code repository of your plugin
            matcher='$data.fileType={FILETYPE FIREFLI}',  # add the query for the firefli types of files your plugin should match
            license='Apache License 2.0'
        )
        return plugin_info

    def process(self, trace, data_context):
        with trace.open(data_type='text', mode='wb') as writer:
            kaitai_utils.write_to_json(trace.open(), writer, kaitai_utils.get_kaitai_class())


if __name__ == '__main__':
    # optional main method to run your plugin with Hansken.py
    # see detail at:
    #  https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/python/hanskenpy.html
    run_with_hanskenpy(Plugin)
