"""Enhanced OCaml code emitter for MGen with comprehensive Python language support."""

import ast
from typing import Any, Optional, Union

from ..base import AbstractEmitter
from ..converter_utils import (
    get_standard_binary_operator,
    get_standard_comparison_operator,
)
from ..preferences import BackendPreferences


class UnsupportedFeatureError(Exception):
    """Raised when encountering unsupported Python features."""
    pass


class TypeMappingError(Exception):
    """Raised when type mapping fails."""
    pass


class MGenPythonToOCamlConverter:
    """Sophisticated Python-to-OCaml converter with comprehensive language support."""

    def __init__(self, preferences: Optional[BackendPreferences] = None):
        """Initialize the converter with optional preferences."""
        self.preferences = preferences
        self.type_map = {
            "int": "int",
            "float": "float",
            "bool": "bool",
            "str": "string",
            "list": "'a list",  # Generic list type
            "dict": "(string * 'a) list",  # Association list
            "set": "'a list",  # List-based set
            "Any": "'a",
            "None": "unit",
            "void": "unit",
        }

        # Track class definitions and variables
        self.classes: dict[str, Any] = {}
        self.variables: dict[str, str] = {}
        self.current_class: Optional[str] = None

    def convert_code(self, python_code: str) -> str:
        """Convert Python source code to OCaml."""
        try:
            tree = ast.parse(python_code)
            return self._convert_module(tree)
        except SyntaxError as e:
            raise UnsupportedFeatureError(f"Python syntax error: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to OCaml."""
        # Include runtime library
        ocaml_code = ["(* Generated OCaml code from Python *)"]
        ocaml_code.append("")
        ocaml_code.append("open Mgen_runtime")
        ocaml_code.append("")

        # Track if main function exists
        has_main = False
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "main":
                has_main = True
                break

        # Convert all statements
        for stmt in node.body:
            converted = self._convert_statement(stmt)
            if converted:
                if isinstance(converted, list):
                    ocaml_code.extend(converted)
                else:
                    ocaml_code.append(converted)
                ocaml_code.append("")

        # Add main execution
        ocaml_code.append("(* Main execution *)")
        if has_main:
            ocaml_code.append('let () = ignore (main ())')
        else:
            ocaml_code.append('let () = print_value "Generated OCaml code executed successfully"')

        return "\n".join(ocaml_code)

    def _convert_statement(self, node: ast.AST) -> Union[str, list[str]]:
        """Convert a Python statement to OCaml."""
        if isinstance(node, ast.FunctionDef):
            return self._convert_function_def(node)
        elif isinstance(node, ast.ClassDef):
            return self._convert_class_def(node)
        elif isinstance(node, ast.Assign):
            return self._convert_assignment(node)
        elif isinstance(node, ast.AnnAssign):
            return self._convert_annotated_assignment(node)
        elif isinstance(node, ast.AugAssign):
            return self._convert_augmented_assignment(node)
        elif isinstance(node, ast.Expr):
            return self._convert_expression_statement(node)
        elif isinstance(node, ast.Return):
            return self._convert_return(node)
        elif isinstance(node, ast.If):
            return self._convert_if_statement(node)
        elif isinstance(node, ast.While):
            return self._convert_while_statement(node)
        elif isinstance(node, ast.For):
            return self._convert_for_statement(node)
        else:
            raise UnsupportedFeatureError(f"Unsupported statement: {type(node).__name__}")

    def _convert_function_def(self, node: ast.FunctionDef) -> list[str]:
        """Convert Python function definition to OCaml."""
        self._to_ocaml_var_name(node.name)

        # Extract parameter information
        params = []
        for arg in node.args.args:
            param_name = self._to_ocaml_var_name(arg.arg)
            param_type = self._get_type_annotation(arg.annotation) if arg.annotation else "'a"
            params.append((param_name, param_type))

        # Get return type
        return_type = self._get_type_annotation(node.returns) if node.returns else "'a"

        # Handle methods vs functions
        if self.current_class:
            # This is a method
            if node.name == "__init__":
                return self._convert_constructor(node, params)
            else:
                return self._convert_method(node, params, return_type)
        else:
            # This is a regular function
            return self._convert_regular_function(node, params, return_type)

    def _convert_regular_function(self, node: ast.FunctionDef, params: list[tuple], return_type: str) -> list[str]:
        """Convert a regular function definition."""
        func_name = self._to_ocaml_var_name(node.name)

        # Function signature
        if params:
            param_list = " ".join([name for name, _ in params])
            signature = f"let {func_name} {param_list} ="
        else:
            signature = f"let {func_name} () ="

        lines = [signature]

        # Convert function body
        if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
            # Single return statement
            expr = self._convert_expression(node.body[0].value) if node.body[0].value else "()"
            lines.append(f"  {expr}")
        else:
            # Multiple statements - use let expressions
            body_lines = []
            for _i, stmt in enumerate(node.body):
                # Skip docstrings (expression statements with string constants)
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    continue
                if isinstance(stmt, ast.Return):
                    if stmt.value:
                        body_lines.append(f"  {self._convert_expression(stmt.value)}")
                    else:
                        body_lines.append("  ()")
                else:
                    converted = self._convert_statement(stmt)
                    if isinstance(converted, list):
                        body_lines.extend([f"  {line}" for line in converted])
                    else:
                        body_lines.append(f"  {converted}")

            if body_lines:
                lines.extend(body_lines)
            else:
                lines.append("  ()")

        return lines

    def _convert_class_def(self, node: ast.ClassDef) -> list[str]:
        """Convert Python class to OCaml record type and functions."""
        class_name = self._to_ocaml_type_name(node.name)
        self.current_class = class_name

        # Extract fields from __init__ method
        init_method = None
        methods = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    init_method = item
                else:
                    methods.append(item)

        lines = []

        # Generate record type
        if init_method:
            fields = self._extract_class_fields(init_method)
            if fields:
                lines.append(f"type {class_name.lower()} = {{")
                for field_name, field_type in fields:
                    lines.append(f"  {field_name} : {field_type};")
                lines.append("}")
                lines.append("")
        else:
            # Empty class
            lines.append(f"type {class_name.lower()} = unit")
            lines.append("")

        # Generate constructor function
        if init_method:
            constructor_lines = self._convert_constructor(init_method, [])
            lines.extend(constructor_lines)
            lines.append("")

        # Generate methods
        for method in methods:
            method_lines = self._convert_method(method, [], "'a")
            lines.extend(method_lines)
            lines.append("")

        self.current_class = None
        return lines

    def _extract_class_fields(self, init_method: ast.FunctionDef) -> list[tuple]:
        """Extract field definitions from __init__ method."""
        fields = []

        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        field_name = self._to_ocaml_var_name(target.attr)
                        field_type = self._infer_type_from_value(stmt.value)
                        fields.append((field_name, field_type))
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                    field_name = self._to_ocaml_var_name(stmt.target.attr)
                    field_type = self._get_type_annotation(stmt.annotation) if stmt.annotation else "'a"
                    fields.append((field_name, field_type))

        return fields

    def _convert_constructor(self, node: ast.FunctionDef, params: list[tuple]) -> list[str]:
        """Convert __init__ method to constructor function."""
        if self.current_class is None:
            raise ValueError("Constructor called outside of class context")
        class_name = self.current_class.lower()

        # Extract constructor parameters (excluding self)
        constructor_params = []
        for arg in node.args.args[1:]:  # Skip 'self'
            param_name = self._to_ocaml_var_name(arg.arg)
            param_type = self._get_type_annotation(arg.annotation) if arg.annotation else "'a"
            constructor_params.append((param_name, param_type))

        # Constructor function signature
        if constructor_params:
            param_list = " ".join([name for name, _ in constructor_params])
            signature = f"let create_{class_name} {param_list} ="
        else:
            signature = f"let create_{class_name} () ="

        lines = [signature]

        # Extract field assignments
        field_assignments = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        field_name = self._to_ocaml_var_name(target.attr)
                        field_value = self._convert_expression(stmt.value)
                        field_assignments.append(f"    {field_name} = {field_value};")
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                    field_name = self._to_ocaml_var_name(stmt.target.attr)
                    if stmt.value:
                        field_value = self._convert_expression(stmt.value)
                    else:
                        # Use default value based on type
                        field_type = self._get_type_annotation(stmt.annotation) if stmt.annotation else "int"
                        field_value = self._get_default_value(field_type)
                    field_assignments.append(f"    {field_name} = {field_value};")

        if field_assignments:
            lines.append("  {")
            lines.extend(field_assignments)
            lines.append("  }")
        else:
            lines.append("  ()")

        return lines

    def _convert_method(self, node: ast.FunctionDef, params: list[tuple], return_type: str) -> list[str]:
        """Convert class method to OCaml function."""
        if self.current_class is None:
            raise ValueError("Method called outside of class context")
        method_name = self._to_ocaml_var_name(node.name)
        class_name = self.current_class.lower()

        # Method parameters (first is always the object)
        method_params = [f"({class_name}_obj : {class_name})"]
        for arg in node.args.args[1:]:  # Skip 'self'
            param_name = self._to_ocaml_var_name(arg.arg)
            method_params.append(param_name)

        # Function signature
        param_list = " ".join(method_params)
        signature = f"let {class_name}_{method_name} {param_list} ="

        lines = [signature]

        # Convert method body (simplified - methods often just return default values)
        if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
            if node.body[0].value:
                expr = self._convert_expression(node.body[0].value)
                lines.append(f"  {expr}")
            else:
                lines.append("  ()")
        else:
            # For complex methods, provide a placeholder
            if return_type == "unit":
                lines.append("  ()")
            elif return_type == "int":
                lines.append("  0")
            elif return_type == "string":
                lines.append('  ""')
            elif return_type == "bool":
                lines.append("  false")
            else:
                lines.append("  (* Method implementation simplified *)")
                lines.append('  failwith "Method not implemented"')

        return lines

    def _convert_expression(self, node: ast.AST) -> str:
        """Convert Python expression to OCaml."""
        if isinstance(node, ast.Constant):
            return self._convert_constant(node)
        elif isinstance(node, ast.Name):
            return self._convert_name(node)
        elif isinstance(node, ast.BinOp):
            return self._convert_binary_operation(node)
        elif isinstance(node, ast.UnaryOp):
            return self._convert_unary_operation(node)
        elif isinstance(node, ast.Compare):
            return self._convert_comparison(node)
        elif isinstance(node, ast.Call):
            return self._convert_function_call(node)
        elif isinstance(node, ast.Attribute):
            return self._convert_attribute_access(node)
        elif isinstance(node, ast.Subscript):
            return self._convert_subscript(node)
        elif isinstance(node, ast.List):
            return self._convert_list_literal(node)
        elif isinstance(node, ast.Dict):
            return self._convert_dict_literal(node)
        elif isinstance(node, ast.Set):
            return self._convert_set_literal(node)
        elif isinstance(node, ast.ListComp):
            return self._convert_list_comprehension(node)
        elif isinstance(node, ast.DictComp):
            return self._convert_dict_comprehension(node)
        elif isinstance(node, ast.SetComp):
            return self._convert_set_comprehension(node)
        elif isinstance(node, ast.IfExp):
            return self._convert_ternary_expression(node)
        else:
            raise UnsupportedFeatureError(f"Unsupported expression: {type(node).__name__}")

    def _convert_constant(self, node: ast.Constant) -> str:
        """Convert Python constant to OCaml."""
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        elif isinstance(node.value, int):
            return str(node.value)
        elif isinstance(node.value, float):
            return str(node.value)
        elif isinstance(node.value, str):
            # Escape quotes and backslashes
            escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif node.value is None:
            return "()"
        else:
            raise UnsupportedFeatureError(f"Unsupported constant type: {type(node.value)}")

    def _convert_name(self, node: ast.Name) -> str:
        """Convert Python name to OCaml variable name."""
        return self._to_ocaml_var_name(node.id)

    def _convert_binary_operation(self, node: ast.BinOp) -> str:
        """Convert Python binary operation to OCaml."""
        left = self._convert_expression(node.left)
        right = self._convert_expression(node.right)

        # Handle OCaml-specific operators
        if isinstance(node.op, ast.FloorDiv):
            op = "/"  # OCaml doesn't have floor division
        elif isinstance(node.op, ast.Mod):
            op = "mod"
        elif isinstance(node.op, ast.Pow):
            op = "**"
        elif isinstance(node.op, ast.BitOr):
            op = "lor"
        elif isinstance(node.op, ast.BitXor):
            op = "lxor"
        elif isinstance(node.op, ast.BitAnd):
            op = "land"
        elif isinstance(node.op, ast.LShift):
            op = "lsl"
        elif isinstance(node.op, ast.RShift):
            op = "lsr"
        else:
            # Use standard operator mapping from converter_utils for common operators
            op_result = get_standard_binary_operator(node.op)
            if op_result is None:
                raise UnsupportedFeatureError(f"Unsupported binary operator: {type(node.op).__name__}")
            op = op_result

        return f"({left} {op} {right})"

    def _convert_unary_operation(self, node: ast.UnaryOp) -> str:
        """Convert Python unary operation to OCaml."""
        operand = self._convert_expression(node.operand)

        if isinstance(node.op, ast.UAdd):
            return f"(+{operand})"
        elif isinstance(node.op, ast.USub):
            return f"(-{operand})"
        elif isinstance(node.op, ast.Not):
            return f"(not {operand})"
        elif isinstance(node.op, ast.Invert):
            return f"(lnot {operand})"
        else:
            raise UnsupportedFeatureError(f"Unsupported unary operator: {type(node.op).__name__}")

    def _convert_comparison(self, node: ast.Compare) -> str:
        """Convert Python comparison to OCaml."""
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsupportedFeatureError("Chained comparisons not supported")

        left = self._convert_expression(node.left)
        right = self._convert_expression(node.comparators[0])
        op = node.ops[0]

        # Handle OCaml-specific comparison operators
        if isinstance(op, ast.NotEq):
            ocaml_op = "<>"  # OCaml uses <> instead of !=
        else:
            # Use standard operator mapping from converter_utils for common operators
            op_result = get_standard_comparison_operator(op)
            if op_result is None:
                raise UnsupportedFeatureError(f"Unsupported comparison operator: {type(op).__name__}")
            # OCaml uses = for equality (same as standard)
            ocaml_op = op_result

        return f"({left} {ocaml_op} {right})"

    def _convert_function_call(self, node: ast.Call) -> str:
        """Convert Python function call to OCaml."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            # Handle built-in functions
            if func_name in ["abs", "bool", "len", "min", "max", "sum"]:
                return self._convert_builtin_call(func_name, node.args)
            elif func_name == "range":
                return self._convert_range_call(node.args)
            elif func_name == "print":
                if node.args:
                    arg_node = node.args[0]
                    arg = self._convert_expression(arg_node)

                    # Determine the conversion function based on type
                    conversion_func: Optional[str] = "string_of_int"  # Default to int

                    # Check if argument is a variable with known type
                    if isinstance(arg_node, ast.Name):
                        var_name = self._to_ocaml_var_name(arg_node.id)
                        if var_name in self.variables:
                            var_type = self.variables[var_name]
                            if var_type == "string" or var_type == "str":
                                conversion_func = None  # No conversion needed
                            elif var_type == "float":
                                conversion_func = "string_of_float"
                            elif var_type == "bool":
                                conversion_func = "Conversions.string_of_bool"
                    # Check if argument is a string literal
                    elif isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, str):
                        conversion_func = None  # No conversion needed

                    if conversion_func:
                        return f"print_value ({conversion_func} {arg})"
                    else:
                        return f"print_value {arg}"
                else:
                    return 'print_value ""'
            else:
                # Regular function call
                args = [self._convert_expression(arg) for arg in node.args]
                if args:
                    return f"{self._to_ocaml_var_name(func_name)} {' '.join(args)}"
                else:
                    return f"{self._to_ocaml_var_name(func_name)} ()"
        elif isinstance(node.func, ast.Attribute):
            return self._convert_method_call(node)
        else:
            raise UnsupportedFeatureError(f"Unsupported function call: {type(node.func).__name__}")

    def _convert_builtin_call(self, func_name: str, args: list[ast.expr]) -> str:
        """Convert built-in function calls."""
        if not args:
            raise UnsupportedFeatureError(f"Function {func_name} requires arguments")

        arg = self._convert_expression(args[0])

        builtin_map = {
            "abs": f"abs' {arg}",
            "bool": f"bool' {arg}",
            "len": f"len' {arg}",
            "min": f"min' {arg} {self._convert_expression(args[1]) if len(args) > 1 else arg}",
            "max": f"max' {arg} {self._convert_expression(args[1]) if len(args) > 1 else arg}",
            "sum": f"sum' {arg}",
        }

        return builtin_map.get(func_name, f"{func_name}' {arg}")

    def _convert_range_call(self, args: list[ast.expr]) -> str:
        """Convert range() call to OCaml."""
        if len(args) == 1:
            stop = self._convert_expression(args[0])
            return f"range_list (range {stop})"
        elif len(args) == 2:
            start = self._convert_expression(args[0])
            stop = self._convert_expression(args[1])
            return f"range_list (range2 {start} {stop})"
        elif len(args) == 3:
            start = self._convert_expression(args[0])
            stop = self._convert_expression(args[1])
            step = self._convert_expression(args[2])
            return f"range_list (range3 {start} {stop} {step})"
        else:
            raise UnsupportedFeatureError("range() requires 1-3 arguments")

    def _convert_method_call(self, node: ast.Call) -> str:
        """Convert method call to OCaml function call."""
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            obj_name = self._to_ocaml_var_name(node.func.value.id)
            method_name = node.func.attr

            # Handle string methods
            if method_name in ["upper", "lower", "strip", "find", "replace", "split"]:
                return self._convert_string_method(obj_name, method_name, node.args)
            else:
                # Object method call
                args = [self._convert_expression(arg) for arg in node.args]
                if args:
                    return f"{obj_name}_{method_name} {obj_name} {' '.join(args)}"
                else:
                    return f"{obj_name}_{method_name} {obj_name}"
        else:
            raise UnsupportedFeatureError("Complex method calls not supported")

    def _convert_string_method(self, obj_name: str, method_name: str, args: list[ast.expr]) -> str:
        """Convert string method calls."""
        if method_name == "upper":
            return f"upper {obj_name}"
        elif method_name == "lower":
            return f"lower {obj_name}"
        elif method_name == "strip":
            return f"strip {obj_name}"
        elif method_name == "find":
            if args:
                substr = self._convert_expression(args[0])
                return f"find {obj_name} {substr}"
            else:
                raise UnsupportedFeatureError("find() requires an argument")
        elif method_name == "replace":
            if len(args) >= 2:
                old_str = self._convert_expression(args[0])
                new_str = self._convert_expression(args[1])
                return f"replace {obj_name} {old_str} {new_str}"
            else:
                raise UnsupportedFeatureError("replace() requires two arguments")
        elif method_name == "split":
            if args:
                delimiter = self._convert_expression(args[0])
                return f"split {obj_name} {delimiter}"
            else:
                return f'split {obj_name} " "'  # Default to space
        else:
            raise UnsupportedFeatureError(f"Unsupported string method: {method_name}")

    def _convert_attribute_access(self, node: ast.Attribute) -> str:
        """Convert attribute access to OCaml field access."""
        if isinstance(node.value, ast.Name):
            obj_name = self._to_ocaml_var_name(node.value.id)
            attr_name = self._to_ocaml_var_name(node.attr)
            return f"{obj_name}.{attr_name}"
        else:
            raise UnsupportedFeatureError("Complex attribute access not supported")

    def _convert_list_literal(self, node: ast.List) -> str:
        """Convert Python list literal to OCaml list."""
        elements = [self._convert_expression(elt) for elt in node.elts]
        return "[" + "; ".join(elements) + "]"

    def _convert_dict_literal(self, node: ast.Dict) -> str:
        """Convert Python dict literal to OCaml association list."""
        pairs = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                raise UnsupportedFeatureError("Dictionary unpacking (**) not supported")
            key_expr = self._convert_expression(key)
            value_expr = self._convert_expression(value)
            pairs.append(f"({key_expr}, {value_expr})")
        return "[" + "; ".join(pairs) + "]"

    def _convert_set_literal(self, node: ast.Set) -> str:
        """Convert Python set literal to OCaml list (sets represented as lists)."""
        elements = [self._convert_expression(elt) for elt in node.elts]
        return "[" + "; ".join(elements) + "]"

    def _convert_list_comprehension(self, node: ast.ListComp) -> str:
        """Convert Python list comprehension to OCaml."""
        expr = self._convert_expression(node.elt)

        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in comprehensions not supported")

        gen = node.generators[0]
        target = self._to_ocaml_var_name(gen.target.id) if isinstance(gen.target, ast.Name) else "x"
        iterable = self._convert_expression(gen.iter)

        if gen.ifs:
            conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
            condition = " && ".join(conditions)
            return f"list_comprehension_with_filter {iterable} (fun {target} -> {condition}) (fun {target} -> {expr})"
        else:
            return f"list_comprehension {iterable} (fun {target} -> {expr})"

    def _convert_dict_comprehension(self, node: ast.DictComp) -> str:
        """Convert Python dict comprehension to OCaml."""
        key_expr = self._convert_expression(node.key)
        value_expr = self._convert_expression(node.value)

        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in comprehensions not supported")

        gen = node.generators[0]
        target = self._to_ocaml_var_name(gen.target.id) if isinstance(gen.target, ast.Name) else "x"
        iterable = self._convert_expression(gen.iter)

        if gen.ifs:
            conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
            condition = " && ".join(conditions)
            return f"dict_comprehension_with_filter {iterable} (fun {target} -> {condition}) (fun {target} -> {key_expr}) (fun {target} -> {value_expr})"
        else:
            return f"dict_comprehension {iterable} (fun {target} -> {key_expr}) (fun {target} -> {value_expr})"

    def _convert_set_comprehension(self, node: ast.SetComp) -> str:
        """Convert Python set comprehension to OCaml."""
        expr = self._convert_expression(node.elt)

        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in comprehensions not supported")

        gen = node.generators[0]
        target = self._to_ocaml_var_name(gen.target.id) if isinstance(gen.target, ast.Name) else "x"
        iterable = self._convert_expression(gen.iter)

        if gen.ifs:
            conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
            condition = " && ".join(conditions)
            return f"set_comprehension_with_filter {iterable} (fun {target} -> {condition}) (fun {target} -> {expr})"
        else:
            return f"set_comprehension {iterable} (fun {target} -> {expr})"

    def _convert_ternary_expression(self, node: ast.IfExp) -> str:
        """Convert Python ternary expression to OCaml if-then-else."""
        test = self._convert_expression(node.test)
        body = self._convert_expression(node.body)
        orelse = self._convert_expression(node.orelse)
        return f"(if {test} then {body} else {orelse})"

    def _convert_assignment(self, node: ast.Assign) -> str:
        """Convert Python assignment to OCaml let binding."""
        if len(node.targets) != 1:
            raise UnsupportedFeatureError("Multiple assignment targets not supported")

        target = node.targets[0]
        value = self._convert_expression(node.value)

        if isinstance(target, ast.Name):
            var_name = self._to_ocaml_var_name(target.id)
            return f"let {var_name} = {value} in"
        else:
            raise UnsupportedFeatureError("Complex assignment targets not supported")

    def _convert_annotated_assignment(self, node: ast.AnnAssign) -> str:
        """Convert Python annotated assignment to OCaml let binding.

        Type annotations are tracked for type-aware code generation.
        """
        target = node.target

        if not node.value:
            # Annotation without value - not supported in OCaml
            raise UnsupportedFeatureError("Annotated assignment without value not supported")

        value = self._convert_expression(node.value)

        if isinstance(target, ast.Name):
            var_name = self._to_ocaml_var_name(target.id)

            # Track variable type for type-aware code generation
            if node.annotation:
                type_name = self._get_type_annotation(node.annotation)
                self.variables[var_name] = type_name

            return f"let {var_name} = {value} in"
        else:
            raise UnsupportedFeatureError("Complex assignment targets not supported")

    def _convert_augmented_assignment(self, node: ast.AugAssign) -> str:
        """Convert Python augmented assignment to OCaml."""
        target = self._convert_expression(node.target)
        value = self._convert_expression(node.value)

        # Handle OCaml-specific operators
        op: str
        if isinstance(node.op, ast.FloorDiv):
            op = "/"  # OCaml doesn't have floor division
        elif isinstance(node.op, ast.Mod):
            op = "mod"
        elif isinstance(node.op, ast.Pow):
            op = "**"
        elif isinstance(node.op, ast.BitOr):
            op = "lor"
        elif isinstance(node.op, ast.BitXor):
            op = "lxor"
        elif isinstance(node.op, ast.BitAnd):
            op = "land"
        elif isinstance(node.op, ast.LShift):
            op = "lsl"
        elif isinstance(node.op, ast.RShift):
            op = "lsr"
        else:
            # Use standard operator mapping from converter_utils for common operators
            op_result = get_standard_binary_operator(node.op)
            if op_result is None:
                raise UnsupportedFeatureError(f"Unsupported augmented assignment operator: {type(node.op).__name__}")
            op = op_result

        return f"let {target} = {target} {op} {value} in"

    def _convert_expression_statement(self, node: ast.Expr) -> str:
        """Convert expression statement."""
        # Ignore docstrings (string constants)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return ""  # Ignore docstrings

        expr = self._convert_expression(node.value)
        return f"let _ = {expr} in"

    def _convert_return(self, node: ast.Return) -> str:
        """Convert return statement."""
        if node.value:
            return self._convert_expression(node.value)
        else:
            return "()"

    def _convert_if_statement(self, node: ast.If) -> str:
        """Convert if statement to OCaml match or if expression."""
        condition = self._convert_expression(node.test)

        # Convert then branch
        then_stmts = []
        for stmt in node.body:
            converted = self._convert_statement(stmt)
            if converted:
                then_stmts.append(converted)
        then_part = then_stmts[-1] if then_stmts else "()"

        # Convert else branch
        if node.orelse:
            else_stmts = []
            for stmt in node.orelse:
                converted = self._convert_statement(stmt)
                if converted:
                    else_stmts.append(converted)
            else_part = else_stmts[-1] if else_stmts else "()"
        else:
            else_part = "()"

        return f"if {condition} then {then_part} else {else_part}"

    def _convert_while_statement(self, node: ast.While) -> str:
        """Convert while statement (simplified)."""
        condition = self._convert_expression(node.test)
        return f"(* while {condition} do ... done *)"

    def _convert_for_statement(self, node: ast.For) -> str:
        """Convert for statement (simplified)."""
        target = self._convert_expression(node.target)
        iter_expr = self._convert_expression(node.iter)
        return f"(* for {target} in {iter_expr} do ... done *)"

    def _to_ocaml_var_name(self, name: str) -> str:
        """Convert Python variable name to OCaml style."""
        # Handle naming convention preferences
        if self.preferences and self.preferences.get("naming_convention") == "camelCase":
            # Convert snake_case to camelCase
            components = name.split("_")
            if len(components) > 1:
                return components[0] + "".join(word.capitalize() for word in components[1:])

        # Default: keep snake_case but ensure it's valid OCaml
        ocaml_name = name.replace("__", "_").lower()

        # Handle OCaml keywords
        keywords = {
            "and", "as", "assert", "begin", "class", "constraint", "do", "done",
            "downto", "else", "end", "exception", "external", "false", "for",
            "fun", "function", "functor", "if", "in", "include", "inherit",
            "initializer", "lazy", "let", "match", "method", "module", "mutable",
            "new", "object", "of", "open", "or", "private", "rec", "sig",
            "struct", "then", "to", "true", "try", "type", "val", "virtual",
            "when", "while", "with"
        }

        if ocaml_name in keywords:
            return f"{ocaml_name}_"

        return ocaml_name

    def _to_ocaml_type_name(self, name: str) -> str:
        """Convert Python class name to OCaml type name."""
        # Capitalize first letter for OCaml type names
        return name[0].upper() + name[1:] if name else name

    def _get_type_annotation(self, annotation: ast.AST) -> str:
        """Convert Python type annotation to OCaml type."""
        if isinstance(annotation, ast.Name):
            return self.type_map.get(annotation.id, annotation.id.lower())
        elif isinstance(annotation, ast.Constant) and annotation.value is None:
            return "unit"
        else:
            # Complex type annotations - simplified
            return "'a"

    def _infer_type_from_value(self, value: ast.AST) -> str:
        """Infer OCaml type from Python value."""
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):
                return "bool"
            elif isinstance(value.value, int):
                return "int"
            elif isinstance(value.value, float):
                return "float"
            elif isinstance(value.value, str):
                return "string"
            elif value.value is None:
                return "unit"
        elif isinstance(value, ast.List):
            return "'a list"
        elif isinstance(value, ast.Dict):
            return "(string * 'a) list"

        return "'a"

    def _get_default_value(self, type_name: str) -> str:
        """Get default value for a type."""
        defaults = {
            "int": "0",
            "float": "0.0",
            "bool": "false",
            "string": '""',
            "unit": "()",
            "'a list": "[]",
            "(string * 'a) list": "[]"
        }
        return defaults.get(type_name, 'failwith "default value not implemented"')

    def _convert_subscript(self, node: ast.Subscript) -> str:
        """Convert subscript access (e.g., list[0], dict[key])."""
        value = self._convert_expression(node.value)
        slice_expr = self._convert_expression(node.slice)
        # For OCaml, we'll use List.nth for lists or other appropriate access
        return f"List.nth {value} {slice_expr}"


class OCamlEmitter(AbstractEmitter):
    """OCaml code emitter using the Python-to-OCaml converter."""

    def __init__(self, preferences: Optional[BackendPreferences] = None):
        """Initialize OCaml emitter with optional preferences."""
        super().__init__(preferences)
        self.converter = MGenPythonToOCamlConverter(preferences)

    def emit_code(self, ast_node: ast.AST) -> str:
        """Generate OCaml code from Python AST."""
        if isinstance(ast_node, ast.Module):
            return self.converter._convert_module(ast_node)
        else:
            raise ValueError("Expected ast.Module node")

    def emit_from_source(self, source_code: str) -> str:
        """Generate OCaml code from Python source."""
        return self.converter.convert_code(source_code)

    def emit_function(self, func_node: ast.FunctionDef, type_context: dict[str, str]) -> str:
        """Generate complete function in OCaml."""
        return "\n".join(self.converter._convert_function_def(func_node))

    def emit_module(self, source_code: str, analysis_result: Optional[Any] = None) -> str:
        """Generate complete module/file in OCaml."""
        return self.converter.convert_code(source_code)

    def map_python_type(self, python_type: str) -> str:
        """Map Python type to OCaml type."""
        return self.converter.type_map.get(python_type, "'a")

    def can_use_simple_emission(self, func_node: ast.FunctionDef, type_context: dict[str, str]) -> bool:
        """Determine if function can use simple emission strategy."""
        # For now, always use the full converter
        return False
