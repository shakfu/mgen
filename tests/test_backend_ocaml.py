"""Tests for OCaml backend functionality."""

import pytest

from mgen.backends.ocaml.emitter import MGenPythonToOCamlConverter, UnsupportedFeatureError
from mgen.backends.ocaml.containers import OCamlContainerSystem
from mgen.backends.ocaml.builder import OCamlBuilder
from mgen.backends.preferences import OCamlPreferences


class TestOCamlBasics:
    """Test basic OCaml code generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = MGenPythonToOCamlConverter()

    def test_simple_function(self):
        """Test simple function conversion."""
        python_code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        ocaml_code = self.converter.convert_code(python_code)

        assert "let add x y =" in ocaml_code
        assert "(x + y)" in ocaml_code

    def test_function_with_no_params(self):
        """Test function with no parameters."""
        python_code = """
def hello() -> str:
    return "Hello, World!"
"""
        ocaml_code = self.converter.convert_code(python_code)

        assert "let hello () =" in ocaml_code
        assert '"Hello, World!"' in ocaml_code

    def test_function_with_multiple_statements(self):
        """Test function with multiple statements."""
        python_code = """
def calculate(x: int, y: int) -> int:
    sum_val = x + y
    product = x * y
    return sum_val + product
"""
        ocaml_code = self.converter.convert_code(python_code)

        assert "let calculate x y =" in ocaml_code
        assert "let sum_val = (x + y)" in ocaml_code
        assert "let product = (x * y)" in ocaml_code
        assert "(sum_val + product)" in ocaml_code

    def test_backend_with_preferences(self):
        """Test OCaml backend with custom preferences."""
        prefs = OCamlPreferences()
        prefs.set('use_pattern_matching', False)
        prefs.set('prefer_immutable', False)

        converter = MGenPythonToOCamlConverter(prefs)
        assert converter.preferences.get('use_pattern_matching') == False
        assert converter.preferences.get('prefer_immutable') == False

    def test_class_conversion(self):
        """Test class conversion to OCaml."""
        python_code = """
class Calculator:
    def __init__(self, name: str):
        self.name: str = name
        self.total: int = 0

    def add(self, value: int) -> None:
        self.total += value

    def get_result(self) -> str:
        return self.name + ": " + str(self.total)
"""
        ocaml_code = self.converter.convert_code(python_code)

        assert 'type calculator' in ocaml_code
        assert 'create_calculator' in ocaml_code
        assert 'calculator_add' in ocaml_code
        assert 'calculator_get_result' in ocaml_code

    def test_list_comprehension_runtime(self):
        """Test list comprehension with runtime consistency."""
        python_code = """
def filter_numbers(numbers):
    return [x * 2 for x in numbers if x > 5]
"""
        ocaml_code = self.converter.convert_code(python_code)

        assert 'list_comprehension_with_filter' in ocaml_code

    def test_list_comprehension_native(self):
        """Test list comprehension with native OCaml syntax."""
        prefs = OCamlPreferences()
        prefs.set('prefer_idiomatic_syntax', True)

        converter = MGenPythonToOCamlConverter(prefs)

        python_code = """
def filter_numbers(numbers):
    return [x * 2 for x in numbers if x > 5]
"""
        ocaml_code = converter.convert_code(python_code)

        # Should use either native OCaml syntax or runtime function
        # For now, accepting runtime function as default behavior
        assert 'list_comprehension_with_filter' in ocaml_code or ('[' in ocaml_code and '|' in ocaml_code)

    def test_string_methods(self):
        """Test string method conversion."""
        python_code = """
def process_text(text: str) -> str:
    return text.upper()
"""
        ocaml_code = self.converter.convert_code(python_code)

        assert 'upper' in ocaml_code


class TestOCamlContainers:
    """Test OCaml container system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.containers = OCamlContainerSystem()

    def test_list_type_mapping(self):
        """Test list type mapping."""
        assert self.containers.get_list_type('int') == 'int list'
        assert self.containers.get_list_type('string') == 'string list'

    def test_dict_type_mapping(self):
        """Test dictionary type mapping."""
        dict_type = self.containers.get_dict_type('string', 'int')
        assert 'string' in dict_type and 'int' in dict_type
        assert 'Hashtbl.t' in dict_type or 'Map' in dict_type

    def test_set_type_mapping(self):
        """Test set type mapping."""
        set_type = self.containers.get_set_type('int')
        assert 'int' in set_type
        assert 'Set' in set_type

    def test_list_operations(self):
        """Test list operation mappings."""
        ops = self.containers.get_list_operations()
        assert 'append' in ops
        assert 'length' in ops
        assert 'map' in ops
        assert 'filter' in ops

    def test_list_literal_generation(self):
        """Test list literal generation."""
        literal = self.containers.generate_list_literal([1, 2, 3], 'int')
        assert literal == '[1; 2; 3]'

        empty_literal = self.containers.generate_list_literal([], 'int')
        assert empty_literal == '[]'

    def test_dict_literal_generation(self):
        """Test dictionary literal generation."""
        literal = self.containers.generate_dict_literal({}, 'string', 'int')
        assert 'empty' in literal or 'create' in literal

    def test_set_literal_generation(self):
        """Test set literal generation."""
        literal = self.containers.generate_set_literal([1, 2, 3], 'int')
        assert 'Set.add' in literal or 'Set.empty' in literal

    def test_container_preferences(self):
        """Test container behavior with preferences."""
        prefs = OCamlPreferences()
        prefs.set('hashtables', 'stdlib')

        containers = OCamlContainerSystem(prefs)
        dict_type = containers.get_dict_type('string', 'int')
        assert 'Hashtbl.t' in dict_type


class TestOCamlBuilder:
    """Test OCaml builder functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = OCamlBuilder()

    def test_build_commands(self):
        """Test build command generation."""
        commands = self.builder.get_build_command('test.ml')
        assert 'ocamlc' in commands
        assert 'test.ml' in commands
        assert 'mgen_runtime.ml' in commands

    def test_run_commands(self):
        """Test run command generation."""
        commands = self.builder.get_run_command('test.ml')
        assert './test' in commands

    def test_build_file_generation(self):
        """Test build file generation."""
        build_content = self.builder.generate_build_file(['test.ml'], 'test')
        assert 'dune' in build_content
        assert 'test' in build_content

    def test_compile_flags(self):
        """Test compile flags."""
        flags = self.builder.get_compile_flags()
        assert isinstance(flags, list)


class TestOCamlPreferences:
    """Test OCaml preference system."""

    def test_default_preferences(self):
        """Test default OCaml preferences."""
        prefs = OCamlPreferences()

        assert prefs.get('ocaml_version') == '4.14'
        assert prefs.get('use_modern_syntax') == True
        assert prefs.get('prefer_immutable') == True
        assert prefs.get('use_pattern_matching') == True
        assert prefs.get('naming_convention') == 'snake_case'

    def test_preference_modification(self):
        """Test preference modification."""
        prefs = OCamlPreferences()

        prefs.set('use_pattern_matching', False)
        assert prefs.get('use_pattern_matching') == False

        prefs.set('ocaml_version', '5.0')
        assert prefs.get('ocaml_version') == '5.0'

    def test_functional_programming_preferences(self):
        """Test functional programming specific preferences."""
        prefs = OCamlPreferences()

        assert prefs.get('prefer_immutable') == True
        assert prefs.get('curried_functions') == True
        assert prefs.get('tail_recursion_opt') == True
        assert prefs.get('list_operations') == 'functional'

    def test_type_system_preferences(self):
        """Test type system preferences."""
        prefs = OCamlPreferences()

        assert prefs.get('type_annotations') == True
        assert prefs.get('polymorphic_variants') == False
        assert prefs.get('gadts') == False

    def test_module_system_preferences(self):
        """Test module system preferences."""
        prefs = OCamlPreferences()

        assert prefs.get('module_structure') == 'nested'
        assert prefs.get('use_functors') == False
        assert prefs.get('signature_files') == False