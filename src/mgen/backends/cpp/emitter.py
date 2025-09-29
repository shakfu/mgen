"""C++ code emitter for MGen with integrated runtime libraries and sophisticated py2cpp conversion.

This module provides sophisticated Python-to-C++ conversion capabilities using STL containers
while maintaining MGen's architecture and API compatibility.

Supported Features:
- Type-annotated function definitions
- Basic data types (int, float, bool, std::string)
- Variable declarations with type annotations
- Advanced arithmetic and comparison operations
- Control structures (if/else, while, for with range)
- Function calls and method calls
- Return statements
- STL container operations (vector, map, set)
- Object-oriented programming (classes, methods, constructors)
- Memory management with RAII
- Comprehensions (list, dict, set) with range iteration and conditional filtering
- String methods with STL string operations
- Augmented assignment operators
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base import AbstractEmitter
from .factory import CppFactory


class UnsupportedFeatureError(Exception):
    """Raised when encountering unsupported Python features."""
    pass


class TypeMappingError(Exception):
    """Raised when type annotation cannot be mapped to C++ type."""
    pass


class MGenPythonToCppConverter:
    """Enhanced Python to C++ converter with MGen STL runtime integration."""

    def __init__(self):
        """Initialize converter with MGen STL runtime support."""
        self.type_mapping = {
            "int": "int",
            "float": "double",
            "bool": "bool",
            "str": "std::string",
            "None": "void",
            "list": "std::vector",  # Will be specialized
            "dict": "std::unordered_map",  # Will be specialized
            "set": "std::unordered_set",   # Will be specialized
        }
        self.current_function: Optional[str] = None
        self.container_variables: Dict[str, Dict[str, Any]] = {}
        self.variable_context: Dict[str, str] = {}  # var_name -> cpp_type
        self.defined_classes: Dict[str, Dict[str, Any]] = {}
        self.iterator_variables: Dict[str, str] = {}
        self.includes_needed = set()
        self.use_runtime = True

    def convert_code(self, source_code: str) -> str:
        """Convert Python source code to C++ code."""
        try:
            tree = ast.parse(source_code)
            return self._convert_module(tree)
        except (UnsupportedFeatureError, TypeMappingError):
            # Re-raise our specific exceptions without wrapping
            raise
        except Exception as e:
            raise UnsupportedFeatureError(f"Failed to convert Python code: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to C++ code."""
        parts = []

        # Check for advanced features to enable appropriate includes
        self.uses_comprehensions = self._uses_comprehensions(node)
        self.uses_classes = self._uses_classes(node)

        # First pass: check for string methods to populate includes_needed
        self._detect_string_methods(node)

        # Add includes
        parts.extend(self._generate_includes())
        parts.append("")

        # Add using namespace for convenience
        parts.append("using namespace std;")
        parts.append("using namespace mgen;")
        parts.append("")

        # Convert functions and classes
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                parts.append(self._convert_function(stmt))
                parts.append("")
            elif isinstance(stmt, ast.ClassDef):
                parts.append(self._convert_class(stmt))
                parts.append("")
            else:
                # Handle other top-level statements if needed
                parts.append(f"// TODO: Handle {type(stmt).__name__}")

        return "\n".join(parts)

    def _generate_includes(self) -> List[str]:
        """Generate necessary C++ includes based on code analysis."""
        includes = [
            "#include <iostream>",
            "#include <string>",
            "#include <vector>",
            "#include <map>",
            "#include <unordered_map>",
            "#include <set>",
            "#include <unordered_set>",
            "#include <algorithm>",
            "#include <memory>"
        ]

        # Add MGen runtime
        includes.append('#include "runtime/mgen_cpp_runtime.hpp"')

        # Add string operations if string methods detected
        if self.includes_needed:
            # StringOps class is included in the runtime
            pass

        return includes

    def _uses_comprehensions(self, node: ast.Module) -> bool:
        """Check if the module uses list/dict/set comprehensions."""
        for n in ast.walk(node):
            if isinstance(n, (ast.ListComp, ast.DictComp, ast.SetComp)):
                return True
        return False

    def _uses_classes(self, node: ast.Module) -> bool:
        """Check if the module uses class definitions."""
        for n in ast.walk(node):
            if isinstance(n, ast.ClassDef):
                return True
        return False

    def _detect_string_methods(self, node: ast.Module) -> None:
        """Detect string method usage to add appropriate includes."""
        for n in ast.walk(node):
            if isinstance(n, ast.Attribute):
                if n.attr in ['upper', 'lower', 'strip', 'find', 'replace', 'split']:
                    self.includes_needed.add('string_ops')

    def _convert_function(self, node: ast.FunctionDef) -> str:
        """Convert a Python function to C++."""
        self.current_function = node.name
        self.variable_context.clear()

        # Get return type
        return_type = self._get_return_type(node)

        # Get parameters with types
        params = []
        for arg in node.args.args:
            param_type = self._get_param_type(arg)
            param_name = arg.arg
            params.append(f"{param_type} {param_name}")
            self.variable_context[param_name] = param_type

        # Generate function body
        body_parts = []
        for stmt in node.body:
            converted = self._convert_statement(stmt)
            if converted.strip():
                body_parts.append(converted)

        body = "\n".join(body_parts)

        # Build function
        param_str = ", ".join(params)
        function = f"{return_type} {node.name}({param_str}) {{\n{self._indent_block(body)}\n}}"

        self.current_function = None
        return function

    def _convert_class(self, node: ast.ClassDef) -> str:
        """Convert a Python class to C++ class."""
        class_name = node.name

        # Extract instance variables and methods
        instance_vars = self._extract_instance_variables(node)
        methods = self._extract_methods(node)

        # Store class info for method resolution
        self.defined_classes[class_name] = {
            "attributes": instance_vars,
            "methods": [m.name for m in methods]
        }

        # Generate class parts
        parts = []
        parts.append(f"class {class_name} {{")
        parts.append("public:")

        # Add instance variables
        if instance_vars:
            parts.append("    // Instance variables")
            for var_name, var_type in instance_vars.items():
                parts.append(f"    {var_type} {var_name};")
            parts.append("")

        # Add constructor if __init__ exists
        init_method = None
        for method in methods:
            if method.name == "__init__":
                init_method = method
                break

        if init_method:
            parts.append(self._generate_constructor(class_name, init_method, instance_vars))
            parts.append("")

        # Add other methods
        for method in methods:
            if method.name != "__init__":
                parts.append(self._generate_method(class_name, method))
                parts.append("")

        parts.append("};")
        return "\n".join(parts)

    def _extract_instance_variables(self, class_node: ast.ClassDef) -> Dict[str, str]:
        """Extract instance variables from __init__ method."""
        instance_vars = {}

        # Find __init__ method
        for stmt in class_node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                # Look for self.attribute assignments
                for init_stmt in stmt.body:
                    if isinstance(init_stmt, ast.AnnAssign) and isinstance(init_stmt.target, ast.Attribute):
                        # self.attr: type = value
                        if (isinstance(init_stmt.target.value, ast.Name) and
                            init_stmt.target.value.id == "self"):
                            attr_name = init_stmt.target.attr
                            attr_type = self._convert_type_annotation(init_stmt.annotation)
                            instance_vars[attr_name] = attr_type
                    elif isinstance(init_stmt, ast.Assign):
                        # self.attr = value
                        for target in init_stmt.targets:
                            if (isinstance(target, ast.Attribute) and
                                isinstance(target.value, ast.Name) and
                                target.value.id == "self"):
                                attr_name = target.attr
                                attr_type = self._infer_type_from_value(init_stmt.value)
                                instance_vars[attr_name] = attr_type

        return instance_vars

    def _extract_methods(self, class_node: ast.ClassDef) -> List[ast.FunctionDef]:
        """Extract method definitions from class."""
        methods = []
        for stmt in class_node.body:
            if isinstance(stmt, ast.FunctionDef):
                methods.append(stmt)
        return methods

    def _generate_constructor(self, class_name: str, init_method: ast.FunctionDef,
                            instance_vars: Dict[str, str]) -> str:
        """Generate C++ constructor from Python __init__."""
        # Get constructor parameters (skip 'self')
        params = []
        for arg in init_method.args.args[1:]:  # Skip 'self'
            param_type = self._get_param_type(arg)
            param_name = arg.arg
            params.append(f"{param_type} {param_name}")
            self.variable_context[param_name] = param_type

        # Generate constructor body
        body_parts = []
        for stmt in init_method.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Attribute):
                # self.attr: type = value
                if (isinstance(stmt.target.value, ast.Name) and
                    stmt.target.value.id == "self"):
                    attr_name = stmt.target.attr
                    if stmt.value:
                        value_expr = self._convert_method_expression(stmt.value, class_name)
                        body_parts.append(f"        this->{attr_name} = {value_expr};")
            elif isinstance(stmt, ast.Assign):
                # self.attr = value
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute) and
                        isinstance(target.value, ast.Name) and
                        target.value.id == "self"):
                        attr_name = target.attr
                        value_expr = self._convert_method_expression(stmt.value, class_name)
                        body_parts.append(f"        this->{attr_name} = {value_expr};")
            else:
                # Other statements in constructor - use method-aware conversion
                converted = self._convert_method_statement(stmt, class_name)
                if converted.strip():
                    body_parts.append(converted)

        # Build constructor
        param_str = ", ".join(params) if params else ""
        body = "\n".join(body_parts)
        constructor = f"    {class_name}({param_str}) {{\n{body}\n    }}"
        return constructor

    def _generate_method(self, class_name: str, method: ast.FunctionDef) -> str:
        """Generate C++ method from Python method."""
        self.current_function = f"{class_name}::{method.name}"

        # Get return type
        return_type = self._get_return_type(method)

        # Get parameters (skip 'self')
        params = []
        for arg in method.args.args[1:]:  # Skip 'self'
            param_type = self._get_param_type(arg)
            param_name = arg.arg
            params.append(f"{param_type} {param_name}")
            self.variable_context[param_name] = param_type

        # Generate method body
        body_parts = []
        for stmt in method.body:
            converted = self._convert_method_statement(stmt, class_name)
            if converted.strip():
                body_parts.append(converted)

        body = "\n".join(body_parts)

        # Build method
        param_str = ", ".join(params)
        method_def = f"    {return_type} {method.name}({param_str}) {{\n{self._indent_block(body)}\n    }}"

        self.current_function = None
        return method_def

    def _convert_method_statement(self, stmt: ast.stmt, class_name: str) -> str:
        """Convert a method statement with class context."""
        if isinstance(stmt, ast.Assign):
            return self._convert_method_assignment(stmt, class_name)
        elif isinstance(stmt, ast.AnnAssign):
            return self._convert_method_annotated_assignment(stmt, class_name)
        elif isinstance(stmt, ast.AugAssign):
            return self._convert_method_aug_assignment(stmt, class_name)
        elif isinstance(stmt, ast.Return):
            return self._convert_method_return(stmt, class_name)
        elif isinstance(stmt, ast.If):
            return self._convert_method_if(stmt, class_name)
        elif isinstance(stmt, ast.Expr):
            expr = self._convert_method_expression(stmt.value, class_name)
            return f"        {expr};"
        else:
            return self._convert_statement(stmt)

    def _convert_method_assignment(self, stmt: ast.Assign, class_name: str) -> str:
        """Convert method assignment with proper self handling."""
        value_expr = self._convert_method_expression(stmt.value, class_name)
        statements = []

        for target in stmt.targets:
            if isinstance(target, ast.Attribute):
                # self.attr = value -> this->attr = value
                if (isinstance(target.value, ast.Name) and target.value.id == "self"):
                    statements.append(f"        this->{target.attr} = {value_expr};")
                else:
                    # obj.attr = value
                    obj_expr = self._convert_method_expression(target.value, class_name)
                    statements.append(f"        {obj_expr}.{target.attr} = {value_expr};")
            elif isinstance(target, ast.Name):
                # Regular variable assignment
                var_type = self._infer_type_from_value(stmt.value)
                self.variable_context[target.id] = var_type
                statements.append(f"        {var_type} {target.id} = {value_expr};")

        return "\n".join(statements)

    def _convert_method_aug_assignment(self, stmt: ast.AugAssign, class_name: str) -> str:
        """Convert augmented assignment in method context with proper self handling."""
        value_expr = self._convert_method_expression(stmt.value, class_name)
        op = self._get_aug_op(stmt.op)

        if isinstance(stmt.target, ast.Attribute):
            # self.attr += value -> this->attr += value
            if (isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self"):
                return f"        this->{stmt.target.attr} {op}= {value_expr};"
            else:
                # obj.attr += value
                obj_expr = self._convert_method_expression(stmt.target.value, class_name)
                return f"        {obj_expr}.{stmt.target.attr} {op}= {value_expr};"
        elif isinstance(stmt.target, ast.Name):
            # Regular variable augmented assignment
            return f"        {stmt.target.id} {op}= {value_expr};"

        return f"        /* Unknown augmented assignment target */"

    def _convert_method_return(self, stmt: ast.Return, class_name: str) -> str:
        """Convert method return statement."""
        if stmt.value:
            value_expr = self._convert_method_expression(stmt.value, class_name)
            return f"        return {value_expr};"
        return "        return;"

    def _convert_method_if(self, stmt: ast.If, class_name: str) -> str:
        """Convert if statement in method context with proper self handling."""
        condition = self._convert_method_expression(stmt.test, class_name)
        then_body = self._convert_method_statements(stmt.body, class_name)
        if_part = f"        if ({condition}) {{\n{then_body}\n        }}"
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif chain
                else_body = self._convert_method_if(stmt.orelse[0], class_name).strip()
                return f"{if_part} else {else_body}"
            else:
                # regular else
                else_body = self._convert_method_statements(stmt.orelse, class_name)
                return f"{if_part} else {{\n{else_body}\n        }}"
        else:
            return if_part

    def _convert_method_statements(self, statements: list, class_name: str) -> str:
        """Convert a list of statements in method context."""
        converted = []
        for stmt in statements:
            converted.append(self._convert_method_statement(stmt, class_name))
        return '\n'.join(converted)

    def _convert_method_expression(self, expr: ast.expr, class_name: str) -> str:
        """Convert method expression with class context."""
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                # self.attr -> this->attr
                return f"this->{expr.attr}"
            else:
                # obj.attr or obj.method()
                obj_expr = self._convert_method_expression(expr.value, class_name)
                return f"{obj_expr}.{expr.attr}"
        elif isinstance(expr, ast.Call):
            # Handle method calls within class context
            if isinstance(expr.func, ast.Attribute):
                if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "self":
                    # self.method() -> handle string methods and other method calls
                    method_name = expr.func.attr
                    args = [self._convert_method_expression(arg, class_name) for arg in expr.args]

                    # Handle string methods on self attributes
                    if method_name in ['upper', 'lower', 'strip', 'find', 'replace', 'split']:
                        obj_expr = f"this->{expr.func.attr}"  # This would be wrong for method calls
                        # Actually, this case shouldn't happen - string methods are called on attributes
                        pass

                    # Regular method calls would need more complex handling
                    return f"/* Method call: {method_name} */"
                else:
                    # Regular method/attribute calls
                    return self._convert_method_call(expr)
            else:
                return self._convert_call(expr)
        elif isinstance(expr, ast.BinOp):
            # Handle binary operations with proper self conversion
            left = self._convert_method_expression(expr.left, class_name)
            right = self._convert_method_expression(expr.right, class_name)

            op_map = {
                ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
                ast.FloorDiv: "/", ast.Mod: "%",
                ast.LShift: "<<", ast.RShift: ">>",
                ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&"
            }

            if isinstance(expr.op, ast.Pow):
                return f"pow({left}, {right})"

            op = op_map.get(type(expr.op), "/*UNKNOWN_OP*/")
            return f"({left} {op} {right})"
        elif isinstance(expr, ast.Compare):
            # Handle comparison operations with proper self conversion
            left = self._convert_method_expression(expr.left, class_name)
            result = left

            for op, comp in zip(expr.ops, expr.comparators):
                op_map: Dict[Any, str] = {
                    ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
                    ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!="
                }
                op_str = op_map.get(type(op), "/*UNKNOWN_OP*/")
                comp_expr = self._convert_method_expression(comp, class_name)
                result = f"({result} {op_str} {comp_expr})"

            return result
        elif isinstance(expr, ast.ListComp):
            return self._convert_method_list_comprehension(expr, class_name)
        elif isinstance(expr, ast.DictComp):
            return self._convert_method_dict_comprehension(expr, class_name)
        elif isinstance(expr, ast.SetComp):
            return self._convert_method_set_comprehension(expr, class_name)
        elif isinstance(expr, ast.Name):
            # Handle regular variable names
            return expr.id
        else:
            return self._convert_expression(expr)

    def _convert_method_list_comprehension(self, expr: ast.ListComp, class_name: str) -> str:
        """Convert list comprehensions in method context using STL and runtime helpers."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_method_expression(arg, class_name) for arg in iter_expr.args]
            range_call = f"Range({', '.join(range_args)})"
            # Create lambda for transformation
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(element_expr, class_name)}; }}"

            if conditions:
                # Comprehension with condition
                condition_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(conditions[0], class_name)}; }}"
                return f"list_comprehension({range_call}, {transform_lambda}, {condition_lambda})"
            else:
                # Simple comprehension
                return f"list_comprehension({range_call}, {transform_lambda})"
        else:
            # Iteration over container (like words)
            container_expr = self._convert_method_expression(iter_expr, class_name)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(element_expr, class_name)}; }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(conditions[0], class_name)}; }}"
                return f"list_comprehension({container_expr}, {transform_lambda}, {condition_lambda})"
            else:
                return f"list_comprehension({container_expr}, {transform_lambda})"

    def _convert_method_dict_comprehension(self, expr: ast.DictComp, class_name: str) -> str:
        """Convert dict comprehensions in method context."""
        # Extract comprehension components
        key_expr = expr.key
        value_expr = expr.value
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            range_args = [self._convert_method_expression(arg, class_name) for arg in iter_expr.args]
            range_call = f"Range({', '.join(range_args)})"
            target_name = target.id if isinstance(target, ast.Name) else "x"

            # Use make_pair for key-value pairs
            key_transform = self._convert_method_expression(key_expr, class_name)
            value_transform = self._convert_method_expression(value_expr, class_name)
            transform_lambda = f"[]({target_name}) {{ return make_pair({key_transform}, {value_transform}); }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(conditions[0], class_name)}; }}"
                return f"dict_comprehension({range_call}, {transform_lambda}, {condition_lambda})"
            else:
                return f"dict_comprehension({range_call}, {transform_lambda})"
        else:
            container_expr = self._convert_method_expression(iter_expr, class_name)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            key_transform = self._convert_method_expression(key_expr, class_name)
            value_transform = self._convert_method_expression(value_expr, class_name)
            transform_lambda = f"[]({target_name}) {{ return make_pair({key_transform}, {value_transform}); }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(conditions[0], class_name)}; }}"
                return f"dict_comprehension({container_expr}, {transform_lambda}, {condition_lambda})"
            else:
                return f"dict_comprehension({container_expr}, {transform_lambda})"

    def _convert_method_set_comprehension(self, expr: ast.SetComp, class_name: str) -> str:
        """Convert set comprehensions in method context."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            range_args = [self._convert_method_expression(arg, class_name) for arg in iter_expr.args]
            range_call = f"Range({', '.join(range_args)})"
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(element_expr, class_name)}; }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(conditions[0], class_name)}; }}"
                return f"set_comprehension({range_call}, {transform_lambda}, {condition_lambda})"
            else:
                return f"set_comprehension({range_call}, {transform_lambda})"
        else:
            container_expr = self._convert_method_expression(iter_expr, class_name)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(element_expr, class_name)}; }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_method_expression(conditions[0], class_name)}; }}"
                return f"set_comprehension({container_expr}, {transform_lambda}, {condition_lambda})"
            else:
                return f"set_comprehension({container_expr}, {transform_lambda})"

    def _convert_statement(self, stmt: ast.stmt) -> str:
        """Convert a Python statement to C++."""
        if isinstance(stmt, ast.Return):
            return self._convert_return(stmt)
        elif isinstance(stmt, ast.Assign):
            return self._convert_assignment(stmt)
        elif isinstance(stmt, ast.AnnAssign):
            return self._convert_annotated_assignment(stmt)
        elif isinstance(stmt, ast.AugAssign):
            return self._convert_aug_assignment(stmt)
        elif isinstance(stmt, ast.If):
            return self._convert_if(stmt)
        elif isinstance(stmt, ast.While):
            return self._convert_while(stmt)
        elif isinstance(stmt, ast.For):
            return self._convert_for(stmt)
        elif isinstance(stmt, ast.Expr):
            return self._convert_expression_statement(stmt)
        else:
            return f"        // TODO: Implement {type(stmt).__name__}"

    def _convert_return(self, stmt: ast.Return) -> str:
        """Convert return statement."""
        if stmt.value:
            value_expr = self._convert_expression(stmt.value)
            return f"        return {value_expr};"
        return "        return;"

    def _convert_assignment(self, stmt: ast.Assign) -> str:
        """Convert assignment statement."""
        value_expr = self._convert_expression(stmt.value)
        statements = []

        for target in stmt.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                var_type = self._infer_type_from_value(stmt.value)
                self.variable_context[var_name] = var_type
                statements.append(f"        {var_type} {var_name} = {value_expr};")
            else:
                # Handle other target types (attributes, subscripts, etc.)
                target_expr = self._convert_expression(target)
                statements.append(f"        {target_expr} = {value_expr};")

        return "\n".join(statements)

    def _convert_annotated_assignment(self, stmt: ast.AnnAssign) -> str:
        """Convert annotated assignment (var: type = value)."""
        if isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
            var_type = self._convert_type_annotation(stmt.annotation)
            self.variable_context[var_name] = var_type

            if stmt.value:
                value_expr = self._convert_expression(stmt.value)
                return f"        {var_type} {var_name} = {value_expr};"
            else:
                return f"        {var_type} {var_name};"
        else:
            # Handle attribute annotations
            target_expr = self._convert_expression(stmt.target)
            if stmt.value:
                value_expr = self._convert_expression(stmt.value)
                return f"        {target_expr} = {value_expr};"
        return ""

    def _convert_method_annotated_assignment(self, stmt: ast.AnnAssign, class_name: str) -> str:
        """Convert annotated assignment in method context (var: type = value)."""
        if isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
            var_type = self._convert_type_annotation(stmt.annotation)
            self.variable_context[var_name] = var_type

            if stmt.value:
                value_expr = self._convert_method_expression(stmt.value, class_name)
                return f"        {var_type} {var_name} = {value_expr};"
            else:
                return f"        {var_type} {var_name};"
        else:
            # Handle attribute annotations
            target_expr = self._convert_method_expression(stmt.target, class_name)
            if stmt.value:
                value_expr = self._convert_method_expression(stmt.value, class_name)
                return f"        {target_expr} = {value_expr};"
        return ""

    def _convert_aug_assignment(self, stmt: ast.AugAssign) -> str:
        """Convert augmented assignment (+=, -=, etc.)."""
        target_expr = self._convert_expression(stmt.target)
        value_expr = self._convert_expression(stmt.value)
        op = self._get_aug_op(stmt.op)
        return f"        {target_expr} {op}= {value_expr};"

    def _convert_if(self, stmt: ast.If) -> str:
        """Convert if statement."""
        condition = self._convert_expression(stmt.test)
        then_body = self._convert_statements(stmt.body)

        if_part = f"        if ({condition}) {{\n{then_body}\n        }}"

        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif chain
                else_body = self._convert_if(stmt.orelse[0]).strip()
                return f"{if_part} else {else_body}"
            else:
                # regular else
                else_body = self._convert_statements(stmt.orelse)
                return f"{if_part} else {{\n{else_body}\n        }}"

        return if_part

    def _convert_while(self, stmt: ast.While) -> str:
        """Convert while loop."""
        condition = self._convert_expression(stmt.test)
        body = self._convert_statements(stmt.body)
        return f"        while ({condition}) {{\n{body}\n        }}"

    def _convert_for(self, stmt: ast.For) -> str:
        """Convert for loop (range-based or container iteration)."""
        target_name = stmt.target.id if isinstance(stmt.target, ast.Name) else "iter_var"

        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name) and stmt.iter.func.id == "range":
            # range() loops
            args = stmt.iter.args
            if len(args) == 1:
                # range(n)
                limit = self._convert_expression(args[0])
                init = f"int {target_name} = 0"
                condition = f"{target_name} < {limit}"
                update = f"{target_name}++"
            elif len(args) == 2:
                # range(start, stop)
                start = self._convert_expression(args[0])
                stop = self._convert_expression(args[1])
                init = f"int {target_name} = {start}"
                condition = f"{target_name} < {stop}"
                update = f"{target_name}++"
            elif len(args) == 3:
                # range(start, stop, step)
                start = self._convert_expression(args[0])
                stop = self._convert_expression(args[1])
                step = self._convert_expression(args[2])
                init = f"int {target_name} = {start}"
                condition = f"{target_name} < {stop}"
                update = f"{target_name} += {step}"
            else:
                raise UnsupportedFeatureError("Invalid range() arguments")

            body = self._convert_statements(stmt.body)
            return f"        for ({init}; {condition}; {update}) {{\n{body}\n        }}"
        else:
            # Range-based for loop for containers
            iter_expr = self._convert_expression(stmt.iter)
            body = self._convert_statements(stmt.body)
            return f"        for (auto {target_name} : {iter_expr}) {{\n{body}\n        }}"

    def _convert_expression_statement(self, stmt: ast.Expr) -> str:
        """Convert expression statement."""
        expr = self._convert_expression(stmt.value)
        return f"        {expr};"

    def _convert_expression(self, expr: ast.expr) -> str:
        """Convert a Python expression to C++."""
        if isinstance(expr, ast.Constant):
            return self._convert_constant(expr)
        elif isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.BinOp):
            return self._convert_binary_op(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._convert_unary_op(expr)
        elif isinstance(expr, ast.BoolOp):
            return self._convert_bool_op(expr)
        elif isinstance(expr, ast.Compare):
            return self._convert_compare(expr)
        elif isinstance(expr, ast.Call):
            return self._convert_call(expr)
        elif isinstance(expr, ast.Attribute):
            return self._convert_attribute(expr)
        elif isinstance(expr, ast.ListComp):
            return self._convert_list_comprehension(expr)
        elif isinstance(expr, ast.DictComp):
            return self._convert_dict_comprehension(expr)
        elif isinstance(expr, ast.SetComp):
            return self._convert_set_comprehension(expr)
        else:
            return f"/* TODO: {type(expr).__name__} */"

    def _convert_constant(self, expr: ast.Constant) -> str:
        """Convert constant values."""
        value = expr.value
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None:
            return "nullptr"
        else:
            return str(value)

    def _convert_binary_op(self, expr: ast.BinOp) -> str:
        """Convert binary operations."""
        left = self._convert_expression(expr.left)
        right = self._convert_expression(expr.right)

        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "/", ast.Mod: "%",
            ast.LShift: "<<", ast.RShift: ">>",
            ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&"
        }

        if isinstance(expr.op, ast.Pow):
            return f"pow({left}, {right})"

        op = op_map.get(type(expr.op), "/*UNKNOWN_OP*/")
        return f"({left} {op} {right})"

    def _convert_unary_op(self, expr: ast.UnaryOp) -> str:
        """Convert unary operations."""
        operand = self._convert_expression(expr.operand)

        op_map = {
            ast.UAdd: "+", ast.USub: "-", ast.Not: "!", ast.Invert: "~"
        }

        op = op_map.get(type(expr.op), "/*UNKNOWN_UNARY*/")
        return f"({op}{operand})"

    def _convert_bool_op(self, expr: ast.BoolOp) -> str:
        """Convert boolean operations."""
        op = " && " if isinstance(expr.op, ast.And) else " || "
        values = [self._convert_expression(v) for v in expr.values]
        return f"({op.join(values)})"

    def _convert_compare(self, expr: ast.Compare) -> str:
        """Convert comparison operations."""
        left = self._convert_expression(expr.left)
        result = left

        op_map = {
            ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",
            ast.In: "/* IN */", ast.NotIn: "/* NOT IN */"
        }

        for op, comparator in zip(expr.ops, expr.comparators):
            right = self._convert_expression(comparator)
            cpp_op = op_map.get(type(op), "/*UNKNOWN_CMP*/")
            result = f"({result} {cpp_op} {right})"

        return result

    def _convert_call(self, expr: ast.Call) -> str:
        """Convert function calls."""
        if isinstance(expr.func, ast.Name):
            func_name = expr.func.id
            args = [self._convert_expression(arg) for arg in expr.args]

            # Map Python built-ins to C++ equivalents
            builtin_map = {
                "print": "cout",
                "len": "mgen::len",
                "abs": "mgen::abs",
                "min": "mgen::min",
                "max": "mgen::max",
                "sum": "mgen::sum",
                "bool": "mgen::bool_value",
                "range": "Range"
            }

            if func_name in builtin_map:
                mapped_name = builtin_map[func_name]
                if func_name == "print":
                    if args:
                        return f"cout << {' << \" \" << '.join(args)} << endl"
                    else:
                        return "cout << endl"
                elif func_name == "range":
                    return f"Range({', '.join(args)})"
                else:
                    return f"{mapped_name}({', '.join(args)})"
            else:
                return f"{func_name}({', '.join(args)})"

        elif isinstance(expr.func, ast.Attribute):
            return self._convert_method_call(expr)
        else:
            return "/* Complex function call */"

    def _convert_method_call(self, expr: ast.Call) -> str:
        """Convert method calls including string methods."""
        if isinstance(expr.func, ast.Attribute):
            # Check if this is a method call on 'self' attribute
            if isinstance(expr.func.value, ast.Attribute) and isinstance(expr.func.value.value, ast.Name) and expr.func.value.value.id == "self":
                # self.attr.method() -> handle string methods on instance variables
                obj_expr = f"this->{expr.func.value.attr}"
            else:
                obj_expr = self._convert_expression(expr.func.value)

            method_name = expr.func.attr
            args = [self._convert_expression(arg) for arg in expr.args]

            # Handle string methods
            if method_name in ['upper', 'lower', 'strip', 'find', 'replace', 'split']:
                if method_name == 'upper':
                    return f"StringOps::upper({obj_expr})"
                elif method_name == 'lower':
                    return f"StringOps::lower({obj_expr})"
                elif method_name == 'strip':
                    if args:
                        return f"StringOps::strip({obj_expr}, {args[0]})"
                    else:
                        return f"StringOps::strip({obj_expr})"
                elif method_name == 'find':
                    return f"StringOps::find({obj_expr}, {args[0]})"
                elif method_name == 'replace':
                    return f"StringOps::replace({obj_expr}, {args[0]}, {args[1]})"
                elif method_name == 'split':
                    if args:
                        return f"StringOps::split({obj_expr}, {args[0]})"
                    else:
                        return f"StringOps::split({obj_expr})"

            # Regular method calls
            if args:
                return f"{obj_expr}.{method_name}({', '.join(args)})"
            else:
                return f"{obj_expr}.{method_name}()"

        return "/* Unknown method call */"

    def _convert_attribute(self, expr: ast.Attribute) -> str:
        """Convert attribute access."""
        obj_expr = self._convert_expression(expr.value)
        return f"{obj_expr}.{expr.attr}"

    def _convert_list_comprehension(self, expr: ast.ListComp) -> str:
        """Convert list comprehensions using STL and runtime helpers."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]
            range_call = f"Range({', '.join(range_args)})"

            # Create lambda for transformation
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_expression(element_expr)}; }}"

            if conditions:
                # With condition
                condition_lambda = f"[]({target_name}) {{ return {self._convert_expression(conditions[0])}; }}"
                return f"list_comprehension({range_call}, {transform_lambda}, {condition_lambda})"
            else:
                # No condition
                return f"list_comprehension({range_call}, {transform_lambda})"
        else:
            # Container iteration (like iterating over a vector)
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_expression(element_expr)}; }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_expression(conditions[0])}; }}"
                return f"list_comprehension({container_expr}, {transform_lambda}, {condition_lambda})"
            else:
                return f"list_comprehension({container_expr}, {transform_lambda})"

    def _convert_dict_comprehension(self, expr: ast.DictComp) -> str:
        """Convert dictionary comprehensions using STL and runtime helpers."""
        # Extract comprehension components
        key_expr = expr.key
        value_expr = expr.value
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]
            range_call = f"Range({', '.join(range_args)})"

            # Create lambda for key-value pairs
            target_name = target.id if isinstance(target, ast.Name) else "x"
            key_val_lambda = f"[]({target_name}) {{ return std::make_pair({self._convert_expression(key_expr)}, {self._convert_expression(value_expr)}); }}"

            if conditions:
                # With condition
                condition_lambda = f"[]({target_name}) {{ return {self._convert_expression(conditions[0])}; }}"
                return f"dict_comprehension({range_call}, {key_val_lambda}, {condition_lambda})"
            else:
                # No condition
                return f"dict_comprehension({range_call}, {key_val_lambda})"
        else:
            # Container iteration (like iterating over a vector)
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            key_val_lambda = f"[]({target_name}) {{ return std::make_pair({self._convert_expression(key_expr)}, {self._convert_expression(value_expr)}); }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_expression(conditions[0])}; }}"
                return f"dict_comprehension({container_expr}, {key_val_lambda}, {condition_lambda})"
            else:
                return f"dict_comprehension({container_expr}, {key_val_lambda})"

    def _convert_set_comprehension(self, expr: ast.SetComp) -> str:
        """Convert set comprehensions using STL and runtime helpers."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]
            range_call = f"Range({', '.join(range_args)})"

            # Create lambda for transformation
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_expression(element_expr)}; }}"

            if conditions:
                # With condition
                condition_lambda = f"[]({target_name}) {{ return {self._convert_expression(conditions[0])}; }}"
                return f"set_comprehension({range_call}, {transform_lambda}, {condition_lambda})"
            else:
                # No condition
                return f"set_comprehension({range_call}, {transform_lambda})"
        else:
            # Container iteration (like iterating over a vector)
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_lambda = f"[]({target_name}) {{ return {self._convert_expression(element_expr)}; }}"

            if conditions:
                condition_lambda = f"[]({target_name}) {{ return {self._convert_expression(conditions[0])}; }}"
                return f"set_comprehension({container_expr}, {transform_lambda}, {condition_lambda})"
            else:
                return f"set_comprehension({container_expr}, {transform_lambda})"

    def _convert_statements(self, statements: List[ast.stmt]) -> str:
        """Convert multiple statements."""
        converted_statements = []
        for stmt in statements:
            converted = self._convert_statement(stmt)
            if converted.strip():
                converted_statements.append(converted)
        return "\n".join(converted_statements)

    def _indent_block(self, text: str) -> str:
        """Add indentation to a block of text."""
        if not text.strip():
            return text
        lines = text.split('\n')
        indented_lines = []
        for line in lines:
            if line.strip():  # Don't indent empty lines
                indented_lines.append(f"    {line}")
            else:
                indented_lines.append(line)
        return '\n'.join(indented_lines)

    def _get_return_type(self, func_node: ast.FunctionDef) -> str:
        """Get return type from function annotation."""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Constant) and func_node.returns.value is None:
                return "void"
            return self._convert_type_annotation(func_node.returns)
        return "auto"

    def _get_param_type(self, arg: ast.arg) -> str:
        """Get parameter type from annotation."""
        if arg.annotation:
            return self._convert_type_annotation(arg.annotation)
        return "auto"

    def _convert_type_annotation(self, annotation: ast.expr) -> str:
        """Convert Python type annotation to C++ type."""
        if isinstance(annotation, ast.Name):
            return self.type_mapping.get(annotation.id, annotation.id)
        elif isinstance(annotation, ast.Constant):
            if annotation.value is None:
                return "void"
            return "auto"
        elif isinstance(annotation, ast.Subscript):
            # Generic types like List[int], Dict[str, int]
            base_type = annotation.value.id if isinstance(annotation.value, ast.Name) else "unknown"
            if base_type == "list":
                element_type = self._convert_type_annotation(annotation.slice)
                return f"std::vector<{element_type}>"
            elif base_type == "dict":
                if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) == 2:
                    key_type = self._convert_type_annotation(annotation.slice.elts[0])
                    val_type = self._convert_type_annotation(annotation.slice.elts[1])
                    return f"std::unordered_map<{key_type}, {val_type}>"
            elif base_type == "set":
                element_type = self._convert_type_annotation(annotation.slice)
                return f"std::unordered_set<{element_type}>"
        return "auto"

    def _infer_type_from_value(self, value: ast.expr) -> str:
        """Infer C++ type from Python value."""
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):
                return "bool"
            elif isinstance(value.value, int):
                return "int"
            elif isinstance(value.value, float):
                return "double"
            elif isinstance(value.value, str):
                return "std::string"
        elif isinstance(value, ast.List):
            return "std::vector<auto>"
        elif isinstance(value, ast.Dict):
            return "std::unordered_map<auto, auto>"
        elif isinstance(value, ast.Set):
            return "std::unordered_set<auto>"
        elif isinstance(value, ast.Call):
            # Infer type from function calls
            if isinstance(value.func, ast.Name):
                func_name = value.func.id
                if func_name in ['abs', 'len', 'sum', 'min', 'max']:
                    return "int"  # Most built-ins return int
                elif func_name == 'bool':
                    return "bool"
                elif func_name in ['str', 'upper', 'lower', 'strip', 'replace']:
                    return "std::string"
                elif func_name == 'range':
                    return "Range"
                else:
                    # Try to infer from function context (if we know the return type)
                    # For now, check if function name suggests a type
                    if func_name.endswith('_int') or func_name in ['factorial', 'calculate', 'compute', 'add', 'subtract', 'multiply']:
                        return "int"
                    elif func_name.endswith('_str') or func_name in ['format', 'get_name', 'to_string']:
                        return "std::string"
                    elif func_name.endswith('_float') or func_name in ['average', 'mean']:
                        return "double"
                    elif func_name.endswith('_bool') or func_name in ['is_valid', 'check']:
                        return "bool"
            elif isinstance(value.func, ast.Attribute):
                # String method calls
                if value.func.attr in ['upper', 'lower', 'strip', 'replace']:
                    return "std::string"
                elif value.func.attr == 'find':
                    return "int"
                elif value.func.attr == 'split':
                    return "std::vector<std::string>"
        elif isinstance(value, ast.BinOp):
            # Try to infer from binary operations
            left_type = self._infer_type_from_value(value.left)
            right_type = self._infer_type_from_value(value.right)

            # If both sides are the same type, return that type
            if left_type != "auto" and left_type == right_type:
                return left_type

            # If one side is int and other is float, result is float
            if (left_type == "int" and right_type == "double") or \
               (left_type == "double" and right_type == "int"):
                return "double"

            # For string concatenation
            if isinstance(value.op, ast.Add) and \
               (left_type == "std::string" or right_type == "std::string"):
                return "std::string"
        return "auto"

    def _get_aug_op(self, op: ast.operator) -> str:
        """Get augmented assignment operator."""
        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "/", ast.Mod: "%",
            ast.LShift: "<<", ast.RShift: ">>",
            ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&"
        }
        return op_map.get(type(op), "/*UNKNOWN_OP*/")


class CppEmitter(AbstractEmitter):
    """Enhanced C++ emitter using MGen Python-to-C++ converter."""

    def __init__(self, preferences=None):
        """Initialize the C++ emitter."""
        super().__init__(preferences)
        self.factory = CppFactory()
        self.converter = MGenPythonToCppConverter()
        self.indent_level = 0
        # Use preferences for indent size if available
        self.indent_size = preferences.get('indent_size', 4) if preferences else 4

    def emit_module(self, source_code: str, analysis_result: Optional[Any] = None) -> str:
        """Emit a complete C++ module from Python source."""
        return self.converter.convert_code(source_code)

    def emit_statement(self, node: ast.stmt) -> str:
        """Emit a C++ statement from a Python AST node."""
        # Delegate to converter for comprehensive statement handling
        return self.converter._convert_statement(node)

    def emit_expression(self, node: ast.expr) -> str:
        """Emit a C++ expression from a Python AST node."""
        # Delegate to converter for comprehensive expression handling
        return self.converter._convert_expression(node)

    def map_python_type(self, python_type: str) -> str:
        """Map Python type to C++ type."""
        return self.converter.type_mapping.get(python_type, "auto")

    def can_use_simple_emission(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> bool:
        """Check if simple emission can be used for this code."""
        # Always use full sophisticated conversion
        return False

    def emit_function(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> str:
        """Emit a C++ function from a Python function definition."""
        # Delegate to converter for comprehensive function handling
        return self.converter._convert_function(func_node)

    def emit_class(self, node: ast.ClassDef) -> str:
        """Emit a C++ class from a Python class definition."""
        # Delegate to converter for comprehensive class handling
        return self.converter._convert_class(node)

    def emit_comprehension(self, node: Union[ast.ListComp, ast.DictComp, ast.SetComp]) -> str:
        """Emit C++ code for comprehensions."""
        if isinstance(node, ast.ListComp):
            return self.converter._convert_list_comprehension(node)
        elif isinstance(node, ast.DictComp):
            return self.converter._convert_dict_comprehension(node)
        elif isinstance(node, ast.SetComp):
            return self.converter._convert_set_comprehension(node)
        else:
            return "/* Unknown comprehension type */"













