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
            id=PluginId(domain='{YOUR_ORGANISATION_DOMAIN}', category='extract', name=plugin_name),
            version='1.0.0',
            description=plugin_description,
            author=Author('{YOUR_NAME}', '{YOUR_EMAIL_ADDRESS}', '{YOUR_ORGANISATION}'),
            maturity=MaturityLevel.PROOF_OF_CONCEPT,
            webpage_url='',  # e.g. url to the code repository of your plugin
            # the matcher specifies in HQL-Lite which traces will be processed by this plugin
            #  e.g. $data.fileType=AppleDouble
            # see also https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/concepts/hql_lite.html#how-to-write-a-matcher
            matcher='$data.fileType={FILETYPE_PROPERTY}',
            license='Apache License 2.0'
        )
        return plugin_info

    def process(self, trace, data_context):
        kaitai_utils.write_kaitai_to_trace(trace)


if __name__ == '__main__':
    # optional main method to run your plugin with Hansken.py
    # see detail at:
    #  https://netherlandsforensicinstitute.github.io/hansken-extraction-plugin-sdk-documentation/latest/dev/python/hanskenpy.html
    run_with_hanskenpy(Plugin)
