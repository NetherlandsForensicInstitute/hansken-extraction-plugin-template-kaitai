import enum
import importlib
import inspect
import json
import os
from io import BufferedWriter
from typing import Any, BinaryIO, Dict, Generator, List, Type

import hansken_extraction_plugin
import yaml
from hansken_extraction_plugin.api.extraction_trace import ExtractionTrace
from hansken_extraction_plugin.api.transformation import RangedTransformation, Range
from json_stream import streamable_dict, streamable_list
from kaitaistruct import KaitaiStruct


def write_kaitai_to_trace(trace: ExtractionTrace, max_byte_array_length: int):
    """
    This method creates traces from a kaitai object tree. It results in a trace containing a JSON representation of the
    object tree and potential child traces containing byte arrays.
    @param trace: ExtractionTrace provided to the plugin. Child traces are added to this.
    @param max_byte_array_length: byte arrays longer than max_byte_array_length are stored as child traces, shorter ones
    are put into the resulting JSON file.
    """

    with trace.open(data_type='text', mode='wb') as writer, trace.open() as data:
        kaitaiclass = _get_kaitai_class()
        kaitai_to_trace_writer = _KaitaiToTraceWriter(writer, trace, max_byte_array_length)
        kaitai_to_trace_writer.write_to_trace(data, kaitaiclass)


def _get_ksy_file():
    path = os.path.relpath(os.path.join(os.path.dirname(__file__), 'structs'))
    # path = 'structs'

    files_in_structs = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    ksy_file_list = list(filter(lambda f: (f.endswith(".ksy")), files_in_structs))

    if len(ksy_file_list) != 1:
        raise ValueError("ERROR: Found ", str(len(ksy_file_list)), " .ksy files in /structs, which is not exactly 1.")
    return os.path.join(path, ksy_file_list[0])


def _get_metadata():
    with open(_get_ksy_file(), 'r') as file:
        return yaml.safe_load(file)['meta']


def _object_has_process_key(searchable_object):
    if type(searchable_object) is dict:
        for key in searchable_object.keys():
            if 'process' in searchable_object:
                return True
            if type(searchable_object[key]) in [list, dict]:
                if _object_has_process_key(searchable_object[key]):
                    return True
    elif type(searchable_object) is list:
        for item in searchable_object:
            if type(item) in [list, dict]:
                if _object_has_process_key(item):
                    return True
    return False


def _token_has_process():
    with open(_get_ksy_file(), 'r') as file:
        toplevel_dict = yaml.safe_load(file)
        return _object_has_process_key(toplevel_dict)


def get_plugin_title_from_metadata():
    metadata = _get_metadata()
    title = metadata['title'] if 'title' in metadata else metadata['id']
    return _to_camel_case(title)


def _get_kaitai_class():
    """
    Finds the Python file generated by Kaitai with the same name as the .ksy file, and returns the top-level class defined in it.
    @return: Class object
    """

    module_file_name = _get_metadata()['id']
    module_path = os.path.dirname(_get_ksy_file()).replace('/', '.')
    module_name = f'{module_path}.{module_file_name}'

    import_result = importlib.import_module(module_name, package=None)

    return list(filter(
        lambda pair: inspect.isclass(pair[1]) and issubclass(pair[1], KaitaiStruct) and not pair[0] == "KaitaiStruct",
        inspect.getmembers(import_result)))[0][1]


class _KaitaiToTraceWriter:
    def __init__(self, writer: BufferedWriter, trace: ExtractionTrace, max_byte_array_length: int):
        self.writer = writer
        self.trace = trace
        self.max_byte_array_length = max_byte_array_length
        self.has_process = _token_has_process()

    @streamable_list
    def _list_to_dict(self, object_list: List[Any], path: str) -> Generator[tuple[str, Any], None, None]:

        for value_index, value in enumerate(object_list):
            yield self._object_to_dict(value, path + f'.[{value_index}]')

    @streamable_dict
    def _object_to_dict(self, instance: Any, path: str) -> Generator[tuple[str, Any], None, None]:
        """
        Recursive helper method that converts an object from the Kaitai tree to (key, value) pairs that are put in
        the resulting JSON file.
        Key: The parameters and property method names
        Value: The parsed value or returning values of the fields and property method names

        @param instance: object that needs parsing to dictionary
        @param path: string representing the jsonpath to the current node in the object tree
        @return: dictionary containing parsed fields and their respective parsed values in a dictionary
        """
        offsets = None
        parameters_dict = _parameters_dict(instance)
        if '_debug' in parameters_dict:
            offsets = parameters_dict['_debug']
        for key, value_object in parameters_dict.items():
            if not _is_public_property(key, value_object):
                continue
            if _is_kaitai_struct(value_object):
                yield _to_lower_camel_case(key), self._object_to_dict(value_object, path + '.' + key)
            elif _is_list(value_object):
                yield _to_lower_camel_case(key), self._list_to_dict(value_object, path)
            elif isinstance(value_object, bytes):
                yield self._process_bytes(value_object, offsets, path, key)
            else:
                yield _to_lower_camel_case(key), _process_value(value_object)

    def _process_bytes(self, value_object, offsets, path, key) -> tuple[str, Any]:
        """
        Method responsible for converting a byte array from the Kaitai object tree to a trace if necessary and / or putting
        it in the resulting JSON output.

        @param value_object: part of the Kaitai object tree that represents a byte array
        @param offsets: the offsets at which the byte array was read in the original inputData
        @param path: JSONpath to this object in the resulting JSON
        @param key: key at which value_object was stored in the Kaitai object tree
        """
        if len(value_object) > self.max_byte_array_length:
            if len(value_object) < hansken_extraction_plugin.runtime.constants.MAX_CHUNK_SIZE:
                length = offsets[key]['end'] - offsets[key]['start']
                child_builder = self.trace.child_builder(path)
                if self.has_process:
                    child_builder.update(data={'raw': value_object}).build()
                    return _to_lower_camel_case(key), f'data block of size: {len(value_object)} (stored as {path})'
                else:
                    child_builder.add_transformation('raw', RangedTransformation([Range(offsets[key]['start'], length)]))
                    child_builder.build()
                    return _to_lower_camel_case(key), f'data block of size: {len(value_object)} (stored as {path})'
            else:
                return _to_lower_camel_case(key), f'data block of size: {len(value_object)} (not added as child trace because size exceeds MAX_CHUNK_SIZE)'
        else:
            return _to_lower_camel_case(key), value_object.hex()


    def to_json_string(self, data_binary: BinaryIO, class_type: Type[KaitaiStruct], path: str) -> str:
        """
        Parses a binary data object to a JSON string

        @param data_binary: binary data containing the file content
        @param class_type: class that contains the parsing to a Kaitai struct
        @param path: string representing the jsonpath to the current entry in the object tree
        @return: JSON string representing contents of data object
        """
        parsed_kaitai_struct = class_type.from_io(data_binary)
        return json.dumps(self._object_to_dict(parsed_kaitai_struct, path), indent=2)

    def write_to_trace(self, data_binary: BinaryIO, class_type: Type[KaitaiStruct], path='$'):
        """
        Writes a binary form of JSON string into a BufferedWriter

        @param data_binary: binary data containing the file content
        @param class_type: class that contains the parsing to a Kaitai struct
        @param path: string representing the jsonpath to the current entry in the object tree
        @return: JSON string representing contents of data object
        """
        self.writer.write(bytes(self.to_json_string(data_binary, class_type, path), "utf-8"))


def _is_public_property(key: str, value: Any):
    return not key.startswith("_") and value is not None


def _parameters_dict(instance: Any) -> Dict[str, Any]:
    """
    Helper method that parses an object in the Kaitai object tree to a dictionary.
    Key: The parameters and property method names
    Value: The original value or returning values of the original fields and property method names

    @param instance: object that needs parsing to dictionary
    @yield: dictionary containing original field names and their respective values in a dictionary
    """
    parameters_dict = vars(instance)
    if _is_kaitai_struct(instance):
        methods = _get_property_methods(type(instance))
        for method in methods:
            parameters_dict[str(method)] = getattr(instance, method)
    return parameters_dict


def _process_value(value_object: Any) -> Any:
    """
    Helper method to process the different types of values to enable their printing in a json

    @param value_object: value of whatever type that might require preprocessing; if not, the value itself is returned
    @return: type that can be dumped in a json
    """
    if type(value_object) is bytes:
        return list(value_object)
    if isinstance(value_object, enum.Enum):
        return {
            "name": value_object.name.upper(),
            "value": value_object.value
        }
    return value_object


def _get_property_methods(class_type: Any) -> List[str]:
    """
    Helper method to obtain method names in a class that are annotated with @property

    @param class_type: class_type that the method obtains @property method names from
    @return: list of method names containing the annotation property
    """
    property_method_names = []
    for name, member in inspect.getmembers(class_type):
        if isinstance(member, property):
            property_method_names.append(name)
    return property_method_names


def _is_kaitai_struct(value_object: Any) -> bool:
    return issubclass(type(value_object), KaitaiStruct)


def _is_list(value_object: Any) -> bool:
    return issubclass(type(value_object), List)


def _to_camel_case(snake_str: str) -> str:
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def _to_lower_camel_case(snake_str: str) -> str:
    camel_string = _to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]
