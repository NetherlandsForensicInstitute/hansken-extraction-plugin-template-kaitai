from hansken_extraction_plugin.api.extraction_plugin import ExtractionPlugin
from hansken_extraction_plugin.api.plugin_info import Author, MaturityLevel, PluginId, PluginInfo
from hansken_extraction_plugin.runtime.extraction_plugin_runner import run_with_hanskenpy
from logbook import Logger

import kaitai_utils


log = Logger(__name__)


class Plugin(ExtractionPlugin):

    def plugin_info(self):
        file_format = kaitai_utils.get_plugin_title_from_metadata()
        no_space_plugin_name = file_format.replace(' ', '_')
        plugin_name = ''.join(letter for letter in no_space_plugin_name if letter.isalnum() or letter == '_')
        plugin_description = f'Extracts "{file_format}" files and attaches its low-level data structure as a JSON text to the trace.'
        plugin_info = PluginInfo(
            id=PluginId(domain='{YOUR DOMAIN}', category='extract', name=plugin_name),
            version='1.0.0',
            description=plugin_description,
            author=Author('Your name', 'your@email.address', 'your organisation'),
            maturity=MaturityLevel.PROOF_OF_CONCEPT,
            webpage_url='',  # e.g. url to the code repository of your plugin
            matcher='$data.fileType={FILETYPE}',  # add the query for the firefli types of files your plugin should match
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
