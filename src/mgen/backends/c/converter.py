"""C code emitter for MGen with integrated runtime libraries and sophisticated py2c conversion.

This module provides sophisticated Python-to-C conversion capabilities adapted from CGen
while maintaining MGen's architecture and API compatibility.

Supported Features:
- Type-annotated function definitions
- Basic data types (int, float, bool, str)
- Variable declarations with type annotations
- Basic arithmetic and comparison operations
- Control structures (if/else, while, for with range)
- Function calls and method calls
- Return statements
- Container operations (list, dict, set)
- Object-oriented programming (classes, methods, constructors)
- Memory management with runtime support
- Comprehensions (list, dict, set) with range iteration and conditional filtering
"""

import ast
from typing import Any, Optional

from ..converter_utils import (
    get_augmented_assignment_operator,
    get_standard_binary_operator,
    get_standard_comparison_operator,
    get_standard_unary_operator,
)
from ..errors import TypeMappingError, UnsupportedFeatureError
from .containers import CContainerSystem


class MGenPythonToCConverter:
    """Enhanced Python to C converter with MGen runtime integration."""

    def __init__(self) -> None:
        """Initialize converter with MGen runtime support."""
        self.type_mapping = {
            "int": "int",
            "float": "double",
            "bool": "bool",
            "str": "char*",
            "None": "void",
            "list": "vec_int",  # Default, will be specialized
            "dict": "map_str_int",  # Default, will be specialized
            "set": "set_int",   # Default, will be specialized
        }
        self.container_system = CContainerSystem()
        self.current_function: Optional[str] = None
        self.container_variables: dict[str, dict[str, Any]] = {}
        self.variable_context: dict[str, str] = {}  # var_name -> c_type
        self.defined_structs: dict[str, dict[str, Any]] = {}
        self.iterator_variables: dict[str, str] = {}
        self.includes_needed: set[str] = set()
        self.use_runtime = True

    def convert_code(self, source_code: str) -> str:
        """Convert Python source code to C code."""
        try:
            tree = ast.parse(source_code)
            return self._convert_module(tree)
        except (UnsupportedFeatureError, TypeMappingError):
            # Re-raise our specific exceptions without wrapping
            raise
        except Exception as e:
            raise UnsupportedFeatureError(f"Failed to convert Python code: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to C code."""
        parts = []

        # Check for comprehensions to enable STC support
        self.uses_comprehensions = self._uses_comprehensions(node)

        # First pass: check for string methods to populate includes_needed
        self._detect_string_methods(node)

        # Add includes
        parts.extend(self._generate_includes())
        parts.append("")

        # Add STC container declarations if needed
        if self._uses_containers(node) or self.uses_comprehensions:
            parts.extend(self._generate_container_declarations())
            parts.append("")

        # Convert functions and classes
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                parts.append(self._convert_function(stmt))
                parts.append("")
            elif isinstance(stmt, ast.ClassDef):
                parts.append(self._convert_class(stmt))
                parts.append("")

        # Add main function if not present
        if not any("main" in part for part in parts):
            parts.append(self._generate_main_function())

        return "\n".join(parts)

    def _detect_string_methods(self, node: ast.AST) -> None:
        """Pre-scan AST to detect string method usage for include generation."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                method_name = child.func.attr

                # Check if this looks like a string method call
                if method_name in ["upper", "lower", "strip", "find", "replace", "split"]:
                    # For pre-scan, we're more liberal - assume any call to these methods is a string method
                    self.includes_needed.add('#include "mgen_string_ops.h"')
                    break  # Only need to add it once

    def _generate_includes(self) -> list[str]:
        """Generate C includes with MGen runtime support."""
        includes = [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <stdbool.h>",
        ]

        if self.use_runtime:
            includes.extend([
                '#include "mgen_error_handling.h"',
                '#include "mgen_python_ops.h"',
                '#include "mgen_memory_ops.h"',
            ])

            if self.container_variables or self._needs_containers():
                includes.append('#include "mgen_stc_bridge.h"')

        # Add STC includes for comprehensions
        if hasattr(self, "uses_comprehensions") and self.uses_comprehensions:
            includes.extend([
                "#define STC_ENABLED",
                '#include "ext/stc/include/stc/vec.h"',
                '#include "ext/stc/include/stc/hmap.h"',
                '#include "ext/stc/include/stc/hset.h"',
            ])

        # Add dynamically needed includes
        includes.extend(sorted(self.includes_needed))

        return includes

    def _generate_container_declarations(self) -> list[str]:
        """Generate STC container template declarations."""
        declarations = []
        declarations.append("// STC container declarations")
        declarations.append("#define STC_ENABLED")
        declarations.append("")

        # Analyze container types needed from existing variables
        container_types = set()
        for var_info in self.container_variables.values():
            if "element_type" in var_info:
                container_types.add(var_info["element_type"])

        # Add types for comprehensions (basic integer support for now)
        if hasattr(self, "uses_comprehensions") and self.uses_comprehensions:
            container_types.add("int")  # Most common case for comprehensions

        # Generate declarations for each type
        for element_type in container_types:
            sanitized = self._sanitize_type_name(element_type)

            # Vector declaration for list comprehensions
            declarations.extend([
                f"#define i_type vec_{sanitized}",
                f"#define i_val {element_type}",
                '#include "ext/stc/include/stc/vec.h"',
                "#undef i_type",
                "#undef i_val",
                ""
            ])

            # Map declaration for dict comprehensions (int -> int)
            declarations.extend([
                f"#define i_type map_{sanitized}_{sanitized}",
                f"#define i_key {element_type}",
                f"#define i_val {element_type}",
                '#include "ext/stc/include/stc/hmap.h"',
                "#undef i_type",
                "#undef i_key",
                "#undef i_val",
                ""
            ])

            # Set declaration for set comprehensions
            declarations.extend([
                f"#define i_type set_{sanitized}",
                f"#define i_key {element_type}",
                '#include "ext/stc/include/stc/hset.h"',
                "#undef i_type",
                "#undef i_key",
                ""
            ])


        return declarations

    def _convert_function(self, node: ast.FunctionDef) -> str:
        """Convert Python function to C function."""
        self.current_function = node.name

        # Build parameter list
        params = []
        for arg in node.args.args:
            param_type = self._get_type_annotation(arg.annotation) if arg.annotation else "int"
            c_type = self.type_mapping.get(param_type, param_type)
            params.append(f"{c_type} {arg.arg}")
            self.variable_context[arg.arg] = c_type

        # Get return type
        return_type = "void"
        if node.returns:
            py_return_type = self._get_type_annotation(node.returns)
            return_type = self.type_mapping.get(py_return_type, py_return_type)

        # Build function signature
        params_str = ", ".join(params) if params else "void"
        signature = f"{return_type} {node.name}({params_str})"

        # Convert function body
        body_lines = []
        for stmt in node.body:
            converted = self._convert_statement(stmt)
            if converted:
                body_lines.extend(converted.split("\n"))

        # Format function
        body = "\n".join(f"    {line}" if line.strip() else "" for line in body_lines)

        self.current_function = None
        return f"{signature} {{\n{body}\n}}"

    def _convert_statement(self, stmt: ast.stmt) -> str:
        """Convert Python statement to C code."""
        if isinstance(stmt, ast.Return):
            return self._convert_return(stmt)
        elif isinstance(stmt, ast.Assign):
            return self._convert_assignment(stmt)
        elif isinstance(stmt, ast.AnnAssign):
            return self._convert_annotated_assignment(stmt)
        elif isinstance(stmt, ast.AugAssign):
            return self._convert_augmented_assignment(stmt)
        elif isinstance(stmt, ast.If):
            return self._convert_if(stmt)
        elif isinstance(stmt, ast.While):
            return self._convert_while(stmt)
        elif isinstance(stmt, ast.For):
            return self._convert_for(stmt)
        elif isinstance(stmt, ast.Expr):
            return self._convert_expression_statement(stmt)
        elif isinstance(stmt, ast.ClassDef):
            return self._convert_class(stmt)
        else:
            return f"/* TODO: Unsupported statement {type(stmt).__name__} */"

    def _convert_return(self, stmt: ast.Return) -> str:
        """Convert return statement."""
        if stmt.value is None:
            return "return;"

        value_expr = self._convert_expression(stmt.value)
        return f"return {value_expr};"

    def _convert_assignment(self, stmt: ast.Assign) -> str:
        """Convert assignment statement."""
        if len(stmt.targets) != 1:
            raise UnsupportedFeatureError("Multiple assignment targets not supported")

        target = stmt.targets[0]

        # Handle attribute assignment (e.g., self.attr = value or obj.attr = value)
        if isinstance(target, ast.Attribute):
            obj = self._convert_expression(target.value)
            attr_name = target.attr
            value_expr = self._convert_expression(stmt.value)

            # If this is a self reference in a method, use pointer access
            if (isinstance(target.value, ast.Name) and target.value.id == "self" and
                self.current_function and "_" in self.current_function):
                return f"self->{attr_name} = {value_expr};"
            else:
                return f"{obj}.{attr_name} = {value_expr};"

        # Handle simple variable assignment
        elif isinstance(target, ast.Name):
            var_name = target.id
            value_expr = self._convert_expression(stmt.value)

            # Infer type from value if not known
            if var_name not in self.variable_context:
                inferred_type = self._infer_expression_type(stmt.value)
                self.variable_context[var_name] = inferred_type
                return f"{inferred_type} {var_name} = {value_expr};"
            else:
                return f"{var_name} = {value_expr};"

        else:
            raise UnsupportedFeatureError("Only simple variable and attribute assignment supported")

    def _convert_annotated_assignment(self, stmt: ast.AnnAssign) -> str:
        """Convert annotated assignment (e.g., x: int = 5 or self.x: int = 5)."""
        # Handle attribute annotation (e.g., self.attr: type = value)
        if isinstance(stmt.target, ast.Attribute):
            obj = self._convert_expression(stmt.target.value)
            attr_name = stmt.target.attr
            type_annotation = self._get_type_annotation(stmt.annotation)
            c_type = self.type_mapping.get(type_annotation, type_annotation)

            if stmt.value:
                value_expr = self._convert_expression(stmt.value)
                # If this is a self reference in a method, use pointer access
                if (isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self" and
                    self.current_function and "_" in self.current_function):
                    return f"self->{attr_name} = {value_expr};"
                else:
                    return f"{obj}.{attr_name} = {value_expr};"
            else:
                # Just a type annotation without assignment
                return f"/* {attr_name}: {c_type} */"

        # Handle simple variable annotation
        elif isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
            type_annotation = self._get_type_annotation(stmt.annotation)
            c_type = self.type_mapping.get(type_annotation, type_annotation)

            self.variable_context[var_name] = c_type

            if stmt.value:
                value_expr = self._convert_expression(stmt.value)
                return f"{c_type} {var_name} = {value_expr};"
            else:
                return f"{c_type} {var_name};"

        else:
            raise UnsupportedFeatureError("Only simple variable and attribute annotation supported")

    def _convert_augmented_assignment(self, stmt: ast.AugAssign) -> str:
        """Convert augmented assignment (+=, -=, etc.) to C syntax."""
        # Handle C-specific operators
        op_str: str
        if isinstance(stmt.op, ast.FloorDiv):
            op_str = "/="  # Floor division maps to regular division in C
        else:
            # Use standard augmented assignment operator mapping from converter_utils
            op_result = get_augmented_assignment_operator(stmt.op)
            if op_result is None:
                raise UnsupportedFeatureError(f"Unsupported augmented assignment operator: {type(stmt.op).__name__}")
            op_str = op_result

        # Check if target is a simple variable
        if isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
            if var_name not in self.variable_context:
                raise TypeMappingError(f"Variable '{var_name}' must be declared before augmented assignment")

            value_expr = self._convert_expression(stmt.value)
            return f"{var_name} {op_str} {value_expr};"

        # Check if target is an attribute (e.g., self.attr += value or obj.attr += value)
        elif isinstance(stmt.target, ast.Attribute):
            obj = self._convert_expression(stmt.target.value)
            attr_name = stmt.target.attr
            value_expr = self._convert_expression(stmt.value)

            # Determine correct access operator (-> for pointers, . for structs)
            if obj == "self":
                return f"self->{attr_name} {op_str} {value_expr};"
            else:
                return f"{obj}.{attr_name} {op_str} {value_expr};"

        else:
            raise UnsupportedFeatureError("Only simple variable and attribute augmented assignments supported")

    def _convert_expression(self, expr: ast.expr) -> str:
        """Convert Python expression to C expression."""
        if isinstance(expr, ast.Constant):
            return self._convert_constant(expr)
        elif isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.BinOp):
            return self._convert_binary_op(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._convert_unary_op(expr)
        elif isinstance(expr, ast.Compare):
            return self._convert_compare(expr)
        elif isinstance(expr, ast.Call):
            return self._convert_call(expr)
        elif isinstance(expr, ast.Attribute):
            return self._convert_attribute(expr)
        elif isinstance(expr, ast.Subscript):
            return self._convert_subscript(expr)
        elif isinstance(expr, ast.ListComp):
            return self._convert_list_comprehension(expr)
        elif isinstance(expr, ast.DictComp):
            return self._convert_dict_comprehension(expr)
        elif isinstance(expr, ast.SetComp):
            return self._convert_set_comprehension(expr)
        elif isinstance(expr, ast.List):
            return self._convert_list_literal(expr)
        elif isinstance(expr, ast.Dict):
            return self._convert_dict_literal(expr)
        elif isinstance(expr, ast.Set):
            return self._convert_set_literal(expr)
        else:
            return f"/* Unsupported expression {type(expr).__name__} */"

    def _convert_constant(self, expr: ast.Constant) -> str:
        """Convert constant values."""
        if isinstance(expr.value, str):
            return f'"{expr.value}"'
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        else:
            return str(expr.value)

    def _convert_binary_op(self, expr: ast.BinOp) -> str:
        """Convert binary operations."""
        left = self._convert_expression(expr.left)
        right = self._convert_expression(expr.right)

        # Handle C-specific operators
        if isinstance(expr.op, ast.Pow):
            # Pow requires math.h
            self.includes_needed.add("#include <math.h>")
            return f"pow({left}, {right})"
        elif isinstance(expr.op, ast.FloorDiv):
            # FloorDiv maps to regular division in C (not exact for negative numbers)
            return f"({left} / {right})"
        else:
            # Use standard operator mapping from converter_utils for common operators
            op = get_standard_binary_operator(expr.op)
            if op is None:
                raise UnsupportedFeatureError(f"Unsupported binary operator: {type(expr.op)}")
            return f"({left} {op} {right})"

    def _convert_unary_op(self, expr: ast.UnaryOp) -> str:
        """Convert unary operations."""
        operand = self._convert_expression(expr.operand)

        # Use standard operator mapping from converter_utils
        op = get_standard_unary_operator(expr.op)
        if op is None:
            raise UnsupportedFeatureError(f"Unsupported unary operator: {type(expr.op)}")
        return f"({op}{operand})"

    def _convert_compare(self, expr: ast.Compare) -> str:
        """Convert comparison operations."""
        if len(expr.ops) != 1 or len(expr.comparators) != 1:
            raise UnsupportedFeatureError("Only simple comparisons supported")

        left = self._convert_expression(expr.left)
        right = self._convert_expression(expr.comparators[0])

        # Use standard operator mapping from converter_utils
        op = get_standard_comparison_operator(expr.ops[0])
        if op is None:
            raise UnsupportedFeatureError(f"Unsupported comparison: {type(expr.ops[0])}")
        return f"({left} {op} {right})"

    def _convert_call(self, expr: ast.Call) -> str:
        """Convert function calls."""
        if isinstance(expr.func, ast.Name):
            func_name = expr.func.id
            args = [self._convert_expression(arg) for arg in expr.args]

            # Check if this is a class instantiation
            if func_name in self.defined_structs:
                # Class instantiation: ClassName() -> ClassName_new()
                args_str = ", ".join(args)
                return f"{func_name}_new({args_str})"

            # Handle built-in functions with runtime support
            elif func_name in ["len", "bool", "abs", "min", "max", "sum"] and self.use_runtime:
                return self._convert_builtin_with_runtime(func_name, args)
            else:
                args_str = ", ".join(args)
                return f"{func_name}({args_str})"

        elif isinstance(expr.func, ast.Attribute):
            # Method call: obj.method() -> ClassName_method(&obj)
            return self._convert_method_call(expr)

        else:
            raise UnsupportedFeatureError("Only simple function calls and method calls supported")

    def _convert_builtin_with_runtime(self, func_name: str, args: list[str]) -> str:
        """Convert built-in functions using MGen runtime."""
        if func_name == "len":
            return f"mgen_len_safe({args[0]}, vec_int_size)"  # Simplified
        elif func_name == "bool":
            return f"mgen_bool_int({args[0]})"
        elif func_name == "abs":
            return f"mgen_abs_int({args[0]})"
        elif func_name in ["min", "max", "sum"]:
            return f"mgen_{func_name}_int_array({args[0]}, {args[1]})"  # Simplified
        else:
            return f"{func_name}({', '.join(args)})"

    def _convert_method_call(self, expr: ast.Call) -> str:
        """Convert method calls: obj.method(args) -> ClassName_method(&obj, args)."""
        if not isinstance(expr.func, ast.Attribute):
            raise UnsupportedFeatureError("Expected attribute access for method call")

        obj_expr = expr.func.value
        method_name = expr.func.attr

        # Convert the object and arguments
        obj = self._convert_expression(obj_expr)
        args = [self._convert_expression(arg) for arg in expr.args]

        # Check if this is a string method call
        if self._is_string_type(obj_expr):
            return self._convert_string_method(obj, method_name, args)

        # Check if this is a list method call
        if self._is_list_type(obj_expr):
            return self._convert_list_method(obj, method_name, args, obj_expr)

        # Try to determine the class type from the object
        # For now, we'll use a simple heuristic - look for known class names
        class_name = None
        if isinstance(obj_expr, ast.Name):
            var_name = obj_expr.id
            # Look in our variable context for the type
            if var_name in self.variable_context:
                var_type = self.variable_context[var_name]
                if var_type in self.defined_structs:
                    class_name = var_type

        if class_name:
            # Method call with known class type
            args_str = ", ".join([f"&{obj}"] + args)
            return f"{class_name}_{method_name}({args_str})"
        else:
            # Fallback - assume it's a simple method call
            args_str = ", ".join(args)
            return f"{obj}_{method_name}({args_str})"

    def _is_string_type(self, expr: ast.expr) -> bool:
        """Check if expression represents a string type."""
        # Check if it's a string literal
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return True

        # Check if it's a variable with string type
        if isinstance(expr, ast.Name):
            var_name = expr.id
            if var_name in self.variable_context:
                var_type = self.variable_context[var_name]
                return var_type in ["str", "char*"]

        # Check if it's an attribute access (e.g., self.text, obj.attr)
        if isinstance(expr, ast.Attribute):
            # For attribute access, look up the attribute in class definitions
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                # This is self.attribute - check if we know this attribute is a string
                attr_name = expr.attr
                # Look through defined structs to find this attribute's type
                for _class_name, class_info in self.defined_structs.items():
                    if attr_name in class_info.get("attributes", {}):
                        attr_type = class_info["attributes"][attr_name]
                        return attr_type in ["str", "char*"]
            else:
                # For obj.attr, try to determine the object type
                obj_expr = expr.value
                if isinstance(obj_expr, ast.Name):
                    obj_name = obj_expr.id
                    if obj_name in self.variable_context:
                        obj_type = self.variable_context[obj_name]
                        if obj_type in self.defined_structs:
                            attr_name = expr.attr
                            class_info = self.defined_structs[obj_type]
                            if attr_name in class_info.get("attributes", {}):
                                attr_type = class_info["attributes"][attr_name]
                                return attr_type in ["str", "char*"]

        return False

    def _convert_string_method(self, obj: str, method_name: str, args: list[str]) -> str:
        """Convert string method calls to appropriate C code."""
        self.includes_needed.add('#include "mgen_string_ops.h"')

        if method_name == "upper":
            if args:
                raise UnsupportedFeatureError("str.upper() takes no arguments")
            return f"mgen_str_upper({obj})"

        elif method_name == "lower":
            if args:
                raise UnsupportedFeatureError("str.lower() takes no arguments")
            return f"mgen_str_lower({obj})"

        elif method_name == "strip":
            if len(args) == 0:
                return f"mgen_str_strip({obj})"
            elif len(args) == 1:
                return f"mgen_str_strip_chars({obj}, {args[0]})"
            else:
                raise UnsupportedFeatureError("str.strip() takes at most one argument")

        elif method_name == "find":
            if len(args) != 1:
                raise UnsupportedFeatureError("str.find() requires exactly one argument")
            return f"mgen_str_find({obj}, {args[0]})"

        elif method_name == "replace":
            if len(args) != 2:
                raise UnsupportedFeatureError("str.replace() requires exactly two arguments")
            return f"mgen_str_replace({obj}, {args[0]}, {args[1]})"

        elif method_name == "split":
            if len(args) == 0:
                return f"mgen_str_split({obj}, NULL)"
            elif len(args) == 1:
                return f"mgen_str_split({obj}, {args[0]})"
            else:
                raise UnsupportedFeatureError("str.split() takes at most one argument")

        else:
            raise UnsupportedFeatureError(f"Unsupported string method: {method_name}")

    def _is_list_type(self, expr: ast.expr) -> bool:
        """Check if expression represents a list/vector type."""
        # Check if it's a list literal
        if isinstance(expr, ast.List):
            return True

        # Check if it's a variable with list type
        if isinstance(expr, ast.Name):
            var_name = expr.id
            if var_name in self.variable_context:
                var_type = self.variable_context[var_name]
                return var_type.startswith("vec_") or var_type == "list"

        return False

    def _convert_list_method(self, obj: str, method_name: str, args: list[str], obj_expr: ast.expr) -> str:
        """Convert list method calls to STC vector operations."""
        # Get the variable name to determine the vec type
        vec_type = "vec_int"  # Default
        if isinstance(obj_expr, ast.Name):
            var_name = obj_expr.id
            if var_name in self.variable_context:
                vec_type = self.variable_context[var_name]

        if method_name == "append":
            if len(args) != 1:
                raise UnsupportedFeatureError("list.append() requires exactly one argument")
            # vec_int_push(&data, value)
            return f"{vec_type}_push(&{obj}, {args[0]})"

        elif method_name == "extend":
            if len(args) != 1:
                raise UnsupportedFeatureError("list.extend() requires exactly one argument")
            # Not implemented yet - would need vec_int_append_range or similar
            raise UnsupportedFeatureError(f"list.extend() is not yet supported in C backend")

        elif method_name == "pop":
            # vec_int_pop(&data) - returns and removes last element
            if len(args) > 1:
                raise UnsupportedFeatureError("list.pop() takes at most one argument")
            if len(args) == 0:
                return f"*{vec_type}_back(&{obj}); {vec_type}_pop(&{obj})"
            else:
                raise UnsupportedFeatureError("list.pop(index) is not yet supported in C backend")

        elif method_name == "clear":
            if args:
                raise UnsupportedFeatureError("list.clear() takes no arguments")
            return f"{vec_type}_clear(&{obj})"

        else:
            raise UnsupportedFeatureError(f"Unsupported list method: {method_name}")

    def _get_type_annotation(self, annotation: ast.expr) -> str:
        """Extract type from annotation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        else:
            return "int"  # Default fallback

    def _infer_expression_type(self, expr: ast.expr) -> str:
        """Infer C type from Python expression."""
        if isinstance(expr, ast.Constant):
            # Note: In Python, bool is a subclass of int, so check bool first
            if isinstance(expr.value, bool):
                return "bool"
            elif isinstance(expr.value, int):
                return "int"
            elif isinstance(expr.value, float):
                return "double"
            elif isinstance(expr.value, str):
                return "char*"
        elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in ["list", "set"]:
                return "vec_int"  # Default
            elif expr.func.id == "dict":
                return "map_str_int"  # Default

        return "int"  # Default fallback

    def _uses_containers(self, node: ast.AST) -> bool:
        """Check if AST uses container types."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in ["list", "dict", "set"]:
                return True
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in ["list", "dict", "set", "append", "extend"]:
                    return True
        return False

    def _needs_containers(self) -> bool:
        """Check if container support is needed."""
        return len(self.container_variables) > 0

    def _uses_comprehensions(self, node: ast.AST) -> bool:
        """Check if the AST contains comprehensions."""
        for child in ast.walk(node):
            if isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                return True
        return False

    def _sanitize_type_name(self, type_name: str) -> str:
        """Sanitize type name for use in STC containers."""
        # Replace special characters and keywords
        sanitized = type_name.replace("*", "ptr").replace(" ", "_")
        if sanitized == "char*":
            return "str"
        elif sanitized == "const char*":
            return "cstr"
        return sanitized

    def _generate_main_function(self) -> str:
        """Generate a default main function."""
        return """int main() {
    printf("Hello from MGen-enhanced C code!\\n");
    return 0;
}"""

    def _convert_if(self, stmt: ast.If) -> str:
        """Convert if statements."""
        condition = self._convert_expression(stmt.test)

        body = []
        for s in stmt.body:
            converted = self._convert_statement(s)
            if converted:
                body.extend(converted.split("\n"))

        result = f"if ({condition}) {{\n"
        for line in body:
            result += f"    {line}\n"
        result += "}"

        if stmt.orelse:
            # Handle elif and else
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # This is an elif
                elif_converted = self._convert_if(stmt.orelse[0])
                result += " else " + elif_converted
            else:
                # This is an else
                result += " else {\n"
                for s in stmt.orelse:
                    converted = self._convert_statement(s)
                    if converted:
                        for line in converted.split("\n"):
                            result += f"    {line}\n"
                result += "}"

        return result

    def _convert_while(self, stmt: ast.While) -> str:
        """Convert while loop."""
        condition = self._convert_expression(stmt.test)
        body = []
        for s in stmt.body:
            converted = self._convert_statement(s)
            if converted:
                body.extend(converted.split("\n"))

        result = f"while ({condition}) {{\n"
        for line in body:
            result += f"    {line}\n"
        result += "}"
        return result

    def _convert_for(self, stmt: ast.For) -> str:
        """Convert for loop (supports range() and container iteration)."""
        if not isinstance(stmt.target, ast.Name):
            raise UnsupportedFeatureError("Only simple loop variables supported")

        var_name = stmt.target.id

        # Handle range-based iteration
        if (isinstance(stmt.iter, ast.Call) and
            isinstance(stmt.iter.func, ast.Name) and
            stmt.iter.func.id == "range"):

            range_args = stmt.iter.args

            if len(range_args) == 1:
                # range(n)
                start, stop, step = "0", self._convert_expression(range_args[0]), "1"
            elif len(range_args) == 2:
                # range(start, stop)
                start, stop, step = self._convert_expression(range_args[0]), self._convert_expression(range_args[1]), "1"
            elif len(range_args) == 3:
                # range(start, stop, step)
                start, stop, step = self._convert_expression(range_args[0]), self._convert_expression(range_args[1]), self._convert_expression(range_args[2])
            else:
                raise UnsupportedFeatureError("Invalid range() arguments")

            self.variable_context[var_name] = "int"

            body = []
            for s in stmt.body:
                converted = self._convert_statement(s)
                if converted:
                    body.extend(converted.split("\n"))

            result = f"for (int {var_name} = {start}; {var_name} < {stop}; {var_name} += {step}) {{\n"
            for line in body:
                result += f"    {line}\n"
            result += "}"
            return result

        # Handle container iteration (for x in container)
        elif isinstance(stmt.iter, ast.Name):
            container_name = stmt.iter.id
            # Use vec_int as default type for now
            index_var = self._generate_temp_var_name("loop_idx")

            self.variable_context[var_name] = "int"

            body = []
            for s in stmt.body:
                converted = self._convert_statement(s)
                if converted:
                    body.extend(converted.split("\n"))

            result = f"for (size_t {index_var} = 0; {index_var} < vec_int_size(&{container_name}); {index_var}++) {{\n"
            result += f"    int {var_name} = *vec_int_at(&{container_name}, {index_var});\n"
            for line in body:
                result += f"    {line}\n"
            result += "}"
            return result

        else:
            raise UnsupportedFeatureError("Only for loops with range() or container iteration supported")

    def _convert_expression_statement(self, stmt: ast.Expr) -> str:
        """Convert expression statement."""
        expr = self._convert_expression(stmt.value)
        return f"{expr};"

    def _convert_attribute(self, expr: ast.Attribute) -> str:
        """Convert attribute access."""
        obj = self._convert_expression(expr.value)

        # If this is a self reference in a method, use pointer access
        if (isinstance(expr.value, ast.Name) and expr.value.id == "self" and
            self.current_function and "_" in self.current_function):
            return f"self->{expr.attr}"

        # Regular struct member access
        return f"{obj}.{expr.attr}"

    def _convert_subscript(self, expr: ast.Subscript) -> str:
        """Convert subscript access."""
        obj = self._convert_expression(expr.value)
        # Handle both Python 3.8 (with ast.Index) and Python 3.9+ (without ast.Index)
        if hasattr(ast, "Index") and isinstance(expr.slice, ast.Index):  # Python < 3.9
            index = self._convert_expression(expr.slice.value)  # type: ignore
        else:  # Python >= 3.9
            index = self._convert_expression(expr.slice)
        return f"{obj}[{index}]"

    def _convert_class(self, node: ast.ClassDef) -> str:
        """Convert Python class to C struct with associated methods."""
        class_name = node.name

        # Analyze class to extract instance variables and methods
        instance_vars = self._extract_instance_variables(node)
        methods = self._extract_methods(node)

        parts = []

        # Generate struct definition
        struct_def = self._generate_struct_definition(class_name, instance_vars)
        parts.append(struct_def)
        parts.append("")

        # Store struct info for later use
        self.defined_structs[class_name] = {
            "instance_vars": instance_vars,
            "attributes": instance_vars,  # For compatibility with string method detection
            "methods": [m.name for m in methods]
        }

        # Generate method declarations
        for method in methods:
            if method.name == "__init__":
                # Constructor
                constructor = self._generate_constructor(class_name, method, instance_vars)
                parts.append(constructor)
            else:
                # Regular method
                method_def = self._generate_method(class_name, method)
                parts.append(method_def)
            parts.append("")

        return "\n".join(parts)

    def _extract_instance_variables(self, class_node: ast.ClassDef) -> dict[str, str]:
        """Extract instance variables from class definition."""
        instance_vars = {}

        # Look for __init__ method to find instance variable assignments
        for stmt in class_node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                for body_stmt in stmt.body:
                    if isinstance(body_stmt, ast.Assign):
                        # Look for self.var = value assignments
                        for target in body_stmt.targets:
                            if (isinstance(target, ast.Attribute) and
                                isinstance(target.value, ast.Name) and
                                target.value.id == "self"):
                                var_name = target.attr
                                # Try to infer type from the assignment
                                var_type = self._infer_expression_type(body_stmt.value)
                                instance_vars[var_name] = var_type
                    elif isinstance(body_stmt, ast.AnnAssign):
                        # Look for self.var: type = value assignments
                        if (isinstance(body_stmt.target, ast.Attribute) and
                            isinstance(body_stmt.target.value, ast.Name) and
                            body_stmt.target.value.id == "self"):
                            var_name = body_stmt.target.attr
                            if body_stmt.annotation:
                                var_type = self._get_type_annotation(body_stmt.annotation)
                                var_type = self.type_mapping.get(var_type, var_type)
                            else:
                                var_type = self._infer_expression_type(body_stmt.value) if body_stmt.value is not None else "void*"
                            instance_vars[var_name] = var_type

        return instance_vars

    def _extract_methods(self, class_node: ast.ClassDef) -> list[ast.FunctionDef]:
        """Extract method definitions from class."""
        methods = []
        for stmt in class_node.body:
            if isinstance(stmt, ast.FunctionDef):
                methods.append(stmt)
        return methods

    def _generate_struct_definition(self, class_name: str, instance_vars: dict[str, str]) -> str:
        """Generate C struct definition for Python class."""
        lines = [f"typedef struct {class_name} {{"]

        if instance_vars:
            for var_name, var_type in instance_vars.items():
                lines.append(f"    {var_type} {var_name};")
        else:
            # Empty struct needs at least one member in C
            lines.append("    char _dummy;  // Empty struct placeholder")

        lines.append(f"}} {class_name};")

        return "\n".join(lines)

    def _generate_constructor(self, class_name: str, init_method: ast.FunctionDef,
                            instance_vars: dict[str, str]) -> str:
        """Generate constructor function for class."""
        # Build parameter list (skip 'self')
        params = []
        for arg in init_method.args.args[1:]:  # Skip 'self'
            param_type = self._get_type_annotation(arg.annotation) if arg.annotation else "int"
            c_type = self.type_mapping.get(param_type, param_type)
            params.append(f"{c_type} {arg.arg}")

        params_str = ", ".join(params) if params else "void"
        signature = f"{class_name} {class_name}_new({params_str})"

        # Generate constructor body
        body_lines = [f"    {class_name} obj;"]

        # Add initialization code from __init__ body
        old_function = self.current_function
        self.current_function = f"{class_name}_new"

        # Set up parameter context
        for arg in init_method.args.args[1:]:
            param_type = self._get_type_annotation(arg.annotation) if arg.annotation else "int"
            c_type = self.type_mapping.get(param_type, param_type)
            self.variable_context[arg.arg] = c_type

        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                # Convert self.var = value to obj.var = value
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute) and
                        isinstance(target.value, ast.Name) and
                        target.value.id == "self"):
                        var_name = target.attr
                        value_expr = self._convert_expression(stmt.value)
                        body_lines.append(f"    obj.{var_name} = {value_expr};")
            elif isinstance(stmt, ast.AnnAssign):
                # Convert self.var: type = value to obj.var = value
                if (isinstance(stmt.target, ast.Attribute) and
                    isinstance(stmt.target.value, ast.Name) and
                    stmt.target.value.id == "self"):
                    var_name = stmt.target.attr
                    if stmt.value:
                        value_expr = self._convert_expression(stmt.value)
                        body_lines.append(f"    obj.{var_name} = {value_expr};")

        body_lines.append("    return obj;")

        self.current_function = old_function

        body = "\n".join(body_lines)
        return f"{signature} {{\n{body}\n}}"

    def _generate_method(self, class_name: str, method: ast.FunctionDef) -> str:
        """Generate C function for class method."""
        method_name = f"{class_name}_{method.name}"

        # Build parameter list (convert 'self' to struct pointer)
        params = [f"{class_name}* self"]
        for arg in method.args.args[1:]:  # Skip 'self'
            param_type = self._get_type_annotation(arg.annotation) if arg.annotation else "int"
            c_type = self.type_mapping.get(param_type, param_type)
            params.append(f"{c_type} {arg.arg}")
            self.variable_context[arg.arg] = c_type

        # Get return type
        return_type = "void"
        if method.returns:
            py_return_type = self._get_type_annotation(method.returns)
            return_type = self.type_mapping.get(py_return_type, py_return_type)

        params_str = ", ".join(params)
        signature = f"{return_type} {method_name}({params_str})"

        # Convert method body
        old_function = self.current_function
        self.current_function = method_name

        body_lines = []
        for stmt in method.body:
            converted = self._convert_method_statement(stmt, class_name)
            if converted:
                body_lines.extend(converted.split("\n"))

        body = "\n".join(f"    {line}" if line.strip() else "" for line in body_lines)

        self.current_function = old_function
        return f"{signature} {{\n{body}\n}}"

    def _convert_method_statement(self, stmt: ast.stmt, class_name: str) -> str:
        """Convert statement inside a method, handling self references."""
        if isinstance(stmt, ast.Assign):
            return self._convert_method_assignment(stmt, class_name)
        elif isinstance(stmt, ast.Return):
            return self._convert_method_return(stmt, class_name)
        else:
            # For other statements, use regular conversion but handle self references
            return self._convert_statement(stmt)

    def _convert_method_assignment(self, stmt: ast.Assign, class_name: str) -> str:
        """Convert assignment in method context."""
        if len(stmt.targets) != 1:
            raise UnsupportedFeatureError("Multiple assignment targets not supported")

        target = stmt.targets[0]

        # Handle self.attr = value
        if (isinstance(target, ast.Attribute) and
            isinstance(target.value, ast.Name) and
            target.value.id == "self"):
            attr_name = target.attr
            value_expr = self._convert_expression(stmt.value)
            return f"self->{attr_name} = {value_expr};"

        # Regular assignment
        return self._convert_assignment(stmt)

    def _convert_method_return(self, stmt: ast.Return, class_name: str) -> str:
        """Convert return statement in method context."""
        if stmt.value is None:
            return "return;"

        value_expr = self._convert_method_expression(stmt.value, class_name)
        return f"return {value_expr};"

    def _convert_method_expression(self, expr: ast.expr, class_name: str) -> str:
        """Convert expression in method context, handling self references."""
        if isinstance(expr, ast.Attribute):
            if (isinstance(expr.value, ast.Name) and expr.value.id == "self"):
                # self.attr becomes self->attr
                return f"self->{expr.attr}"

        # For other expressions, use regular conversion
        return self._convert_expression(expr)

    def _convert_list_comprehension(self, node: ast.ListComp) -> str:
        """Convert list comprehension to C loop with STC list operations.

        [expr for target in iter if condition] becomes:
        vec_type result = {0};
        for (...) {
            if (condition) {
                vec_type_push(&result, expr);
            }
        }
        """
        # Generate unique temporary variable name for the result
        temp_var = self._generate_temp_var_name("comp_result")

        # Infer result element type from the expression
        result_element_type = self._infer_expression_type(node.elt)
        result_container_type = f"vec_{self._sanitize_type_name(result_element_type)}"

        # Process the single generator (comprehensions can have multiple, but we'll start simple)
        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in list comprehensions not yet supported")

        generator = node.generators[0]

        # Extract loop variable and iterable
        if not isinstance(generator.target, ast.Name):
            raise UnsupportedFeatureError("Only simple loop variables supported in comprehensions")

        loop_var = generator.target.id

        # Handle range-based iteration (most common case)
        if (isinstance(generator.iter, ast.Call) and
            isinstance(generator.iter.func, ast.Name) and
            generator.iter.func.id == "range"):

            # Generate range-based for loop
            range_args = generator.iter.args
            if len(range_args) == 1:
                start = "0"
                end = self._convert_expression(range_args[0])
                step = "1"
            elif len(range_args) == 2:
                start = self._convert_expression(range_args[0])
                end = self._convert_expression(range_args[1])
                step = "1"
            elif len(range_args) == 3:
                start = self._convert_expression(range_args[0])
                end = self._convert_expression(range_args[1])
                step = self._convert_expression(range_args[2])
            else:
                raise UnsupportedFeatureError("Invalid range() arguments in comprehension")

            loop_code = f"for (int {loop_var} = {start}; {loop_var} < {end}; {loop_var} += {step})"
            loop_var_decl = None  # No separate variable declaration needed for range

        # Handle iteration over container variables (e.g., for x in numbers)
        elif isinstance(generator.iter, ast.Name):
            container_name = generator.iter.id
            # Use vec_int as default type for now (TODO: proper type inference)
            container_size_call = f"vec_int_size(&{container_name})"
            container_at_call = f"vec_int_at(&{container_name}, __idx_{temp_var})"

            # Generate index-based iteration
            index_var = f"__idx_{temp_var}"
            loop_code = f"for (size_t {index_var} = 0; {index_var} < {container_size_call}; {index_var}++)"
            loop_var_decl = f"int {loop_var} = *{container_at_call};\n        "

        else:
            raise UnsupportedFeatureError("Non-range iterables in comprehensions not yet supported")

        # Handle conditions (if any)
        condition_code = ""
        if generator.ifs:
            if len(generator.ifs) > 1:
                raise UnsupportedFeatureError("Multiple conditions in comprehensions not yet supported")

            condition = generator.ifs[0]
            condition_expr = self._convert_expression(condition)
            condition_code = f"if ({condition_expr}) "

        # Convert the expression
        expr_str = self._convert_expression(node.elt)

        # Generate the comprehension code differently based on iteration type
        if loop_var_decl:
            # Container iteration requires extracting the element first
            comp_code = f"""{{
    {result_container_type} {temp_var} = {{0}};
    {loop_code} {{
        {loop_var_decl}{condition_code}vec_{self._sanitize_type_name(result_element_type)}_push(&{temp_var}, {expr_str});
    }}
    {temp_var}}}"""
        else:
            # Range-based iteration is simpler
            comp_code = f"""{{
    {result_container_type} {temp_var} = {{0}};
    {loop_code} {{
        {condition_code}vec_{self._sanitize_type_name(result_element_type)}_push(&{temp_var}, {expr_str});
    }}
    {temp_var}}}"""

        return comp_code

    def _convert_dict_comprehension(self, node: ast.DictComp) -> str:
        """Convert dictionary comprehension to C loop with STC hashmap operations.

        {key_expr: value_expr for target in iter if condition} becomes:
        map_key_value result = {0};
        for (...) {
            if (condition) {
                map_key_value_insert(&result, key_expr, value_expr);
            }
        }
        """
        # Generate unique temporary variable name
        temp_var = self._generate_temp_var_name("dict_comp_result")

        # Infer key and value types
        key_type = self._infer_expression_type(node.key)
        value_type = self._infer_expression_type(node.value)
        result_container_type = f"map_{self._sanitize_type_name(key_type)}_{self._sanitize_type_name(value_type)}"

        # Process the single generator
        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in dict comprehensions not yet supported")

        generator = node.generators[0]

        # Extract loop variable and iterable
        if not isinstance(generator.target, ast.Name):
            raise UnsupportedFeatureError("Only simple loop variables supported in comprehensions")

        loop_var = generator.target.id

        # Handle range-based iteration
        if (isinstance(generator.iter, ast.Call) and
            isinstance(generator.iter.func, ast.Name) and
            generator.iter.func.id == "range"):

            range_args = generator.iter.args
            if len(range_args) == 1:
                start = "0"
                end = self._convert_expression(range_args[0])
                step = "1"
            elif len(range_args) == 2:
                start = self._convert_expression(range_args[0])
                end = self._convert_expression(range_args[1])
                step = "1"
            elif len(range_args) == 3:
                start = self._convert_expression(range_args[0])
                end = self._convert_expression(range_args[1])
                step = self._convert_expression(range_args[2])
            else:
                raise UnsupportedFeatureError("Invalid range() arguments in comprehension")

            loop_code = f"for (int {loop_var} = {start}; {loop_var} < {end}; {loop_var} += {step})"
        else:
            raise UnsupportedFeatureError("Non-range iterables in dict comprehensions not yet supported")

        # Handle conditions (if any)
        condition_code = ""
        if generator.ifs:
            if len(generator.ifs) > 1:
                raise UnsupportedFeatureError("Multiple conditions in dict comprehensions not yet supported")

            condition = generator.ifs[0]
            condition_expr = self._convert_expression(condition)
            condition_code = f"if ({condition_expr}) "

        # Convert the key and value expressions
        key_str = self._convert_expression(node.key)
        value_str = self._convert_expression(node.value)

        # Generate the comprehension code
        comp_code = f"""{{
    {result_container_type} {temp_var} = {{0}};
    {loop_code} {{
        {condition_code}{result_container_type}_insert(&{temp_var}, {key_str}, {value_str});
    }}
    {temp_var}}}"""

        return comp_code

    def _convert_set_comprehension(self, node: ast.SetComp) -> str:
        """Convert set comprehension to C loop with STC hset operations.

        {expr for target in iter if condition} becomes:
        set_type result = {0};
        for (...) {
            if (condition) {
                set_type_insert(&result, expr);
            }
        }
        """
        # Generate unique temporary variable name
        temp_var = self._generate_temp_var_name("set_comp_result")

        # Infer element type from the expression
        element_type = self._infer_expression_type(node.elt)
        result_container_type = f"set_{self._sanitize_type_name(element_type)}"

        # Process the single generator
        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in set comprehensions not yet supported")

        generator = node.generators[0]

        # Extract loop variable and iterable
        if not isinstance(generator.target, ast.Name):
            raise UnsupportedFeatureError("Only simple loop variables supported in set comprehensions")

        loop_var = generator.target.id

        # Handle range-based iteration
        if (isinstance(generator.iter, ast.Call) and
            isinstance(generator.iter.func, ast.Name) and
            generator.iter.func.id == "range"):

            range_args = generator.iter.args
            if len(range_args) == 1:
                start = "0"
                end = self._convert_expression(range_args[0])
                step = "1"
            elif len(range_args) == 2:
                start = self._convert_expression(range_args[0])
                end = self._convert_expression(range_args[1])
                step = "1"
            elif len(range_args) == 3:
                start = self._convert_expression(range_args[0])
                end = self._convert_expression(range_args[1])
                step = self._convert_expression(range_args[2])
            else:
                raise UnsupportedFeatureError("Invalid range() arguments in comprehension")

            loop_code = f"for (int {loop_var} = {start}; {loop_var} < {end}; {loop_var} += {step})"
        else:
            raise UnsupportedFeatureError("Non-range iterables in set comprehensions not yet supported")

        # Handle conditions (if any)
        condition_code = ""
        if generator.ifs:
            if len(generator.ifs) > 1:
                raise UnsupportedFeatureError("Multiple conditions in set comprehensions not yet supported")

            condition = generator.ifs[0]
            condition_expr = self._convert_expression(condition)
            condition_code = f"if ({condition_expr}) "

        # Convert the expression
        expr_str = self._convert_expression(node.elt)

        # Generate the comprehension code
        comp_code = f"""{{
    {result_container_type} {temp_var} = {{0}};
    {loop_code} {{
        {condition_code}{result_container_type}_insert(&{temp_var}, {expr_str});
    }}
    {temp_var}}}"""

        return comp_code

    def _convert_list_literal(self, expr: ast.List) -> str:
        """Convert list literal to C STC vector initialization.

        Empty lists [] become {0}
        Non-empty lists [1, 2, 3] become initialization code
        """
        if not expr.elts:
            # Empty list - return STC zero-initialization
            return "{0}"
        else:
            # Non-empty list - generate initialization with elements
            # For now, just return {0} and let caller handle adding elements
            # TODO: Support inline initialization for simple cases
            return "{0}"

    def _convert_dict_literal(self, expr: ast.Dict) -> str:
        """Convert dict literal to C STC hashmap initialization.

        Empty dicts {} become {0}
        Non-empty dicts need element-by-element insertion
        """
        if not expr.keys:
            # Empty dict - return STC zero-initialization
            return "{0}"
        else:
            # Non-empty dict - generate initialization with key-value pairs
            # For now, return {0} and let caller handle inserting pairs
            # TODO: Support inline initialization for simple cases
            return "{0}"

    def _convert_set_literal(self, expr: ast.Set) -> str:
        """Convert set literal to C STC hashset initialization.

        Empty sets set() become {0} (handled via Call conversion)
        Non-empty sets {1, 2, 3} need element-by-element insertion
        """
        if not expr.elts:
            # Empty set - return STC zero-initialization
            return "{0}"
        else:
            # Non-empty set - generate initialization with elements
            # For now, return {0} and let caller handle adding elements
            # TODO: Support inline initialization for simple cases
            return "{0}"

    def _generate_temp_var_name(self, prefix: str) -> str:
        """Generate a unique temporary variable name."""
        import time
        return f"{prefix}_{int(time.time() * 1000000) % 1000000}"
