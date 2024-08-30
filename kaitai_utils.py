import enum
import importlib
import inspect
import json
import os
from io import BufferedWriter
from os.path import isfile, join
from typing import Any, BinaryIO, Dict, Generator, List, Type

import hansken_extraction_plugin
import kaitaistruct
import yaml
from hansken_extraction_plugin.api.extraction_trace import ExtractionTrace
from json_stream import streamable_dict, streamable_list
from kaitaistruct import KaitaiStruct


def get_ksy_file():
    path = os.path.relpath(os.path.join(os.path.dirname(__file__), 'structs'))
    # path = 'structs'

    files_in_structs = [f for f in os.listdir(path) if isfile(join(path, f))]
    ksy_file_list = list(filter(lambda f: (f.endswith(".ksy")), files_in_structs))

    if len(ksy_file_list) != 1:
        raise ValueError("ERROR: Found ", str(len(ksy_file_list)), " .ksy files in /structs, which is not exactly 1.")
    return os.path.join(path, ksy_file_list[0])


def get_plugin_title_from_metadata():
    with open(get_ksy_file(), 'r') as file:
        ksy = yaml.safe_load(file)

    metadata = ksy["meta"]
    title = metadata["title"]
    if title is not None:
        return _to_camel_case(title)
    else:
        return _to_camel_case(metadata["id"])


class JsonWriter:
    def __init__(self, writer: BufferedWriter, trace: ExtractionTrace):
        self.writer = writer
        self.trace = trace

    @streamable_list
    def _list_to_dict(self, object_list: List[Any], path: str) -> Generator[
        tuple[str, Any], None, None]:
        for value_index, value in enumerate(object_list):
            yield self._object_to_dict(value, path + f'.[{value_index}]')

    @streamable_dict
    def _object_to_dict(self, instance: Any, path: str) -> Generator[Dict[str, Any], None, None]:
        """
        Recursive helper method that parses an object to a dictionary.
        Key: The parameters and property method names
        Value: The parsed value or returning values of the fields and property method names

        @param instance: object that needs parsing to dictionary
        @param path: string representing the jsonpath to the current node in the object tree
        @return: dictionary containing parsed fields and their respective parsed values in a dictionary
        """
        parameters_dict = _parameters_dict(instance)
        for key, value_object in parameters_dict.items():
            if is_public_property(key, value_object):
                if _is_kaitai_struct(value_object):
                    yield _to_lower_camel_case(key), self._object_to_dict(value_object, path + '.' + key)
                elif _is_list(value_object):
                    yield _to_lower_camel_case(key), self._list_to_dict(value_object, path)
                elif isinstance(value_object, bytes):
                    if len(value_object) < hansken_extraction_plugin.runtime.constants.MAX_CHUNK_SIZE:
                        child_builder = self.trace.child_builder(path)
                        child_builder.update(data={'raw': value_object}).build()
                    yield _to_lower_camel_case(key), "data block of size: " + str(len(value_object))
                else:
                    yield _to_lower_camel_case(key), _process_value(value_object)

    def to_json_string(self, data_binary: BinaryIO, class_type: Type[KaitaiStruct], path: str) -> str:
        """
        Parses a binary data object to a JSON string

        @param data_binary: binary data containing the file content
        @param class_type: class that contains the parsing to a KaiTai struct
        @param path: string representing the jsonpath to the current entry in the object tree
        @return: JSON string representing contents of data object
        """
        parsed_kaitai_struct = class_type.from_io(data_binary)
        return json.dumps(self._object_to_dict(parsed_kaitai_struct, path), indent=2)

    def write_to_json(self, data_binary: BinaryIO, class_type: Type[KaitaiStruct], path='$'):
        """
        Writes a binary form of JSON string into a BufferedWriter

        @param data_binary: binary data containing the file content
        @param writer: bufferedWriter to write the binary form of the JSON string to
        @param class_type: class that contains the parsing to a KaiTai struct
        @param path: string representing the jsonpath to the current entry in the object tree
        @return: JSON string representing contents of data object
        """
        self.writer.write(bytes(self.to_json_string(data_binary, class_type, path), "utf-8"))


def get_kaitai_class():
    """
    Finds the Python file generated by Kaitai with the same name as the .ksy file, and returns the top-level class defined in it.
    @return: Class object
    """

    ksy_filename = get_ksy_file().split(".")[0].replace('/', '.')

    import_result = importlib.import_module(ksy_filename, package=None)

    return list(filter(
        lambda pair: inspect.isclass(pair[1]) and issubclass(pair[1], kaitaistruct.KaitaiStruct) and not pair[
                                                                                                             0] == "KaitaiStruct",
        inspect.getmembers(import_result)))[0][1]


def is_public_property(key: str, value: Any):
    return not key.startswith("_") and value is not None


def _parameters_dict(instance: Any) -> Dict[str, Any]:
    """
    Helper method that parses an object to a dictionary.
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
    return issubclass(type(value_object), kaitaistruct.KaitaiStruct)


def _is_list(value_object: Any) -> bool:
    return issubclass(type(value_object), List)


def _to_camel_case(snake_str: str) -> str:
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def _to_lower_camel_case(snake_str: str) -> str:
    camel_string = _to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]
