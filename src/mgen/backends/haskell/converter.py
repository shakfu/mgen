"""Enhanced Haskell code emitter for MGen with comprehensive Python language support."""

import ast
from typing import Any, Optional

from ..converter_utils import (
    get_standard_binary_operator,
    get_standard_comparison_operator,
)
from ..errors import TypeMappingError, UnsupportedFeatureError
from ..preferences import BackendPreferences


class MGenPythonToHaskellConverter:
    """Sophisticated Python-to-Haskell converter with comprehensive language support."""

    def __init__(self, preferences: Optional[BackendPreferences] = None):
        """Initialize the converter with optional preferences."""
        self.preferences = preferences
        self.type_map = {
            "int": "Int",
            "float": "Double",
            "bool": "Bool",
            "str": "String",
            "list": "[a]",  # Generic list type
            "dict": "Dict String a",  # Dictionary with String keys
            "set": "Set a",  # Generic set type
            "void": "()",
            "None": "()",
            "NoneType": "()",
        }
        self.data_types: dict[str, Any] = {}  # Track data type definitions for classes
        self.current_function: Optional[str] = None  # Track current function context
        self.declared_vars: set[str] = set()  # Track declared variables in current function
        self.needed_imports: set[str] = set()  # Track which imports are needed

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to CamelCase."""
        # If it's already CamelCase, keep it as is
        if snake_str[0].isupper():
            return snake_str
        components = snake_str.split("_")
        return "".join(word.capitalize() for word in components)

    def _to_haskell_function_name(self, function_name: str) -> str:
        """Convert Python function name to Haskell function name (camelCase)."""
        if function_name == "main":
            return "main"

        # Check for Haskell reserved keywords
        haskell_keywords = {
            "case", "class", "data", "default", "deriving", "do", "else",
            "foreign", "if", "import", "in", "infix", "infixl", "infixr",
            "instance", "let", "module", "newtype", "of", "then", "type",
            "where", "as", "qualified", "hiding"
        }

        components = function_name.split("_")
        if len(components) == 1:
            base_name = function_name
        else:
            base_name = components[0] + "".join(word.capitalize() for word in components[1:])

        # If it's a reserved keyword, append an underscore
        if base_name.lower() in haskell_keywords:
            return base_name + "_"
        return base_name

    def _to_haskell_var_name(self, var_name: str) -> str:
        """Convert Python variable name to Haskell variable name (camelCase)."""
        return self._to_haskell_function_name(var_name)

    def convert_code(self, python_code: str) -> str:
        """Convert Python code to Haskell."""
        try:
            tree = ast.parse(python_code)
            return self._convert_module(tree)
        except UnsupportedFeatureError:
            # Re-raise UnsupportedFeatureError without wrapping
            raise
        except Exception as e:
            raise TypeMappingError(f"Failed to convert Python code: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to Haskell."""
        parts = []

        # Reset needed imports for this module
        self.needed_imports = set()

        # Scan for needed imports
        self._scan_for_imports(node)

        # Add language extensions if needed
        extensions = []
        if any(isinstance(item, ast.ClassDef) for item in node.body):
            extensions.append("{-# LANGUAGE OverloadedStrings #-}")
        if self.needed_imports:
            extensions.append("{-# LANGUAGE FlexibleInstances #-}")

        if extensions:
            parts.extend(extensions)
            parts.append("")

        # Add module declaration
        parts.append("module Main where")
        parts.append("")

        # Add imports
        base_imports = [
            "import MGenRuntime",
            "import Control.Monad (foldM)",
            "import qualified Data.Map as Map",
            "import qualified Data.Set as Set",
            "import Data.Map (Map)",
            "import Data.Set (Set)"
        ]

        for imp in base_imports:
            parts.append(imp)
        parts.append("")

        # Convert classes first (they become data type definitions)
        for item in node.body:
            if isinstance(item, ast.ClassDef):
                data_def = self._convert_class(item)
                parts.append(data_def)
                parts.append("")

        # Convert functions
        functions = []
        has_main = False
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "main":
                    has_main = True
                func_code = self._convert_function(item)
                functions.append(func_code)

        # Add functions to parts
        parts.extend(functions)

        # Add main function if not present
        if not has_main:
            main_func = '''main :: IO ()
main = printValue "Generated Haskell code executed successfully"'''
            parts.append(main_func)

        return "\n".join(parts)

    def _scan_for_imports(self, node: ast.AST) -> None:
        """Scan AST for features that require imports."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    # String methods, dict methods, etc.
                    self.needed_imports.add("string_ops")
                elif isinstance(child.func, ast.Name):
                    if child.func.id in ["len", "abs", "min", "max", "sum"]:
                        self.needed_imports.add("builtins")
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                self.needed_imports.add("comprehensions")
            elif isinstance(child, ast.AugAssign):
                self.needed_imports.add("augassign")

    def _convert_class(self, node: ast.ClassDef) -> str:
        """Convert Python class to Haskell data type with functions."""
        class_name = self._to_camel_case(node.name)

        # Extract fields from __init__ method
        fields = []
        constructor = None
        methods = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    constructor = item
                    # Extract field assignments from constructor
                    for stmt in item.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                    field_name = self._to_haskell_var_name(target.attr)
                                    field_type = self._infer_type_from_node(stmt.value)
                                    fields.append(f"    {field_name} :: {field_type}")
                        elif isinstance(stmt, ast.AnnAssign):
                            if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                                field_name = self._to_haskell_var_name(stmt.target.attr)
                                field_type = self._convert_type_annotation(stmt.annotation)
                                fields.append(f"    {field_name} :: {field_type}")
                else:
                    methods.append(item)

        # Handle empty class
        if not fields:
            fields = ["    dummy :: ()"]

        # Store class info for method generation
        self.data_types[class_name] = {
            "fields": [field.strip().split(" :: ")[0] for field in fields],
            "constructor": constructor,
            "methods": methods
        }

        # Generate data type definition
        parts = []
        parts.append(f"data {class_name} = {class_name}")
        parts.append("  { " + "\n  , ".join(field.strip() for field in fields))
        parts.append("  } deriving (Show, Eq)")

        # Generate constructor function
        if constructor:
            constructor_func = self._convert_constructor(class_name, constructor)
            parts.append("")
            parts.append(constructor_func)

        # Generate methods
        for method in methods:
            method_func = self._convert_method(class_name, method)
            parts.append("")
            parts.append(method_func)

        return "\n".join(parts)

    def _convert_constructor(self, class_name: str, constructor: ast.FunctionDef) -> str:
        """Convert Python __init__ method to Haskell constructor function."""
        func_name = f"new{class_name}"

        # Extract parameters (skip self)
        params = []
        for arg in constructor.args.args[1:]:  # Skip 'self'
            param_name = self._to_haskell_var_name(arg.arg)
            param_type = "a"  # Default generic type
            if arg.annotation:
                param_type = self._convert_type_annotation(arg.annotation)
            params.append(f"{param_name} :: {param_type}")

        param_names = [param.split(" :: ")[0] for param in params]
        param_types = " -> ".join([param.split(" :: ")[1] for param in params]) if params else ""

        if param_types:
            signature = f"{func_name} :: {param_types} -> {class_name}"
        else:
            signature = f"{func_name} :: {class_name}"

        # Generate constructor body
        field_assignments = []
        for stmt in constructor.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        field_name = self._to_haskell_var_name(target.attr)
                        value = self._convert_expression(stmt.value)
                        field_assignments.append(f"{field_name} = {value}")
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                    field_name = self._to_haskell_var_name(stmt.target.attr)
                    if stmt.value:
                        value = self._convert_expression(stmt.value)
                    else:
                        value = "undefined"  # Default value
                    field_assignments.append(f"{field_name} = {value}")

        if not field_assignments:
            field_assignments = ["dummy = ()"]

        if param_names:
            param_pattern = " " + " ".join(param_names)
        else:
            param_pattern = ""
        body = f"{func_name}{param_pattern} = {class_name} {{ {', '.join(field_assignments)} }}"

        return f"{signature}\n{body}"

    def _convert_method(self, class_name: str, method: ast.FunctionDef) -> str:
        """Convert Python instance method to Haskell function."""
        method_name = self._to_haskell_function_name(method.name)

        # Extract parameters (skip self)
        params = []
        for arg in method.args.args[1:]:  # Skip 'self'
            param_name = self._to_haskell_var_name(arg.arg)
            param_type = "a"  # Default generic type
            if arg.annotation:
                param_type = self._convert_type_annotation(arg.annotation)
            params.append((param_name, param_type))

        # Determine return type
        return_type = "()"
        if method.returns:
            return_type = self._convert_type_annotation(method.returns)

        # Build function signature
        param_types = [param[1] for param in params]
        all_types = [class_name] + param_types + [return_type]
        signature = f"{method_name} :: " + " -> ".join(all_types)

        # Convert function body - for now, return undefined for methods with side effects
        # In Haskell, we can't modify object state directly due to immutability
        if return_type == "()":
            body = "()"  # Void methods return unit
        else:
            body = "undefined"  # Non-void methods need proper implementation

        param_names = ["obj"] + [param[0] for param in params]
        param_pattern = " " + " ".join(param_names)

        implementation = f"{method_name}{param_pattern} = {body}"

        return f"{signature}\n{implementation}"

    def _convert_function(self, node: ast.FunctionDef) -> str:
        """Convert Python function to Haskell."""
        func_name = self._to_haskell_function_name(node.name)

        # Handle main function specially
        if node.name == "main":
            self.current_function = "main"
            self.declared_vars = set()

            do_lines = []

            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    # Ignore return statements in main (Haskell main returns void)
                    continue

                # Skip docstrings (expression statements with string constants)
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    continue

                converted_stmt = self._convert_statement(stmt)
                if not converted_stmt:
                    continue

                # Categorize and add to do notation, preserving order
                if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                    # It's a let binding
                    do_lines.append(f"  let {converted_stmt}")
                else:
                    # It's an IO action or other statement
                    do_lines.append(f"  {converted_stmt}")

            # Build main body with do notation if needed
            signature = "main :: IO ()"

            if not do_lines:
                body = 'main = printValue "No statements"'
            elif len(do_lines) == 1 and not do_lines[0].strip().startswith("let"):
                # Single IO action, no do notation needed
                body = f"main = {do_lines[0].strip()}"
            else:
                # Use do notation
                body = "main = do\n" + "\n".join(do_lines)

            self.current_function = None
            self.declared_vars = set()
            return f"{signature}\n{body}"

        # Extract parameters
        params = []
        for arg in node.args.args:
            param_name = self._to_haskell_var_name(arg.arg)
            param_type = "a"  # Default generic type
            if arg.annotation:
                param_type = self._convert_type_annotation(arg.annotation)
            params.append((param_name, param_type))

        # Determine return type
        return_type = "a"  # Default generic type
        if node.returns:
            return_type = self._convert_type_annotation(node.returns)
        elif node.name == "main":
            return_type = "IO ()"

        # Build function signature
        if params:
            param_types = [param[1] for param in params]
            all_types = param_types + [return_type]
            signature = f"{func_name} :: " + " -> ".join(all_types)
        else:
            signature = f"{func_name} :: {return_type}"

        # Convert function body
        self.current_function = func_name
        self.declared_vars = set()

        # Filter out docstrings first
        filtered_body = []
        for stmt in node.body:
            # Skip docstrings (expression statements with string constants)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                continue
            filtered_body.append(stmt)

        # Check for early return pattern BEFORE converting statements
        # Pattern: if cond: return X; return Y  ->  if cond then X else Y
        if (len(filtered_body) == 2 and
            isinstance(filtered_body[0], ast.If) and
            len(filtered_body[0].body) == 1 and
            isinstance(filtered_body[0].body[0], ast.Return) and
            isinstance(filtered_body[1], ast.Return) and
            not filtered_body[0].orelse):
            # Convert directly to if-expression
            condition = self._convert_expression(filtered_body[0].test)
            then_expr = filtered_body[0].body[0].value
            else_expr = filtered_body[1].value
            if then_expr and else_expr:
                then_value = self._convert_expression(then_expr)
                else_value = self._convert_expression(else_expr)
                body = f"if {condition} then {then_value} else {else_value}"
            else:
                # Fall back to normal conversion if return values are None
                then_value = self._convert_expression(then_expr) if then_expr else "()"
                else_value = self._convert_expression(else_expr) if else_expr else "()"
                body = f"if {condition} then {then_value} else {else_value}"
        else:
            # Normal conversion path
            body_stmts = []
            for stmt in filtered_body:
                converted_stmt = self._convert_statement(stmt)
                if converted_stmt:
                    body_stmts.append(converted_stmt)

            # Handle return statements and function body
            if not body_stmts:
                body = "undefined"
            elif len(body_stmts) == 1:
                body = body_stmts[0]
            else:
                # Multiple statements - use let expressions
                body = "let\n    " + "\n    ".join(body_stmts[:-1]) + "\n  in " + body_stmts[-1]

        param_names = [param[0] for param in params]
        if param_names:
            param_pattern = " " + " ".join(param_names)
        else:
            param_pattern = ""

        implementation = f"{func_name}{param_pattern} = {body}"

        self.current_function = None
        self.declared_vars = set()

        return f"{signature}\n{implementation}"

    def _convert_statement(self, node: ast.stmt) -> str:
        """Convert Python statement to Haskell."""
        if isinstance(node, ast.Return):
            if node.value:
                return self._convert_expression(node.value)
            else:
                return "()"

        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    var_name = self._to_haskell_var_name(target.id)
                    value = self._convert_expression(node.value)
                    return f"{var_name} = {value}"
                else:
                    return "-- Complex assignment target"
            else:
                return "-- Multiple assignment targets"

        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                var_name = self._to_haskell_var_name(node.target.id)
                if node.value:
                    value = self._convert_expression(node.value)
                    return f"{var_name} = {value}"
                else:
                    return f"{var_name} = undefined"  # Type annotation without value
            else:
                return "-- Complex annotated assignment"

        elif isinstance(node, ast.Expr):
            # Expression statements are already properly converted
            expr = self._convert_expression(node.value)
            return expr

        elif isinstance(node, ast.AugAssign):
            return self._convert_augmented_assignment(node)

        elif isinstance(node, ast.If):
            return self._convert_if_statement(node)

        elif isinstance(node, ast.While):
            return self._convert_while_statement(node)

        elif isinstance(node, ast.For):
            return self._convert_for_statement(node)

        else:
            raise UnsupportedFeatureError(f"Unsupported statement type: {type(node).__name__}")

    def _convert_expression(self, node: ast.expr) -> str:
        """Convert Python expression to Haskell."""
        if isinstance(node, ast.Constant):
            return self._convert_constant(node)

        elif isinstance(node, ast.Name):
            return self._to_haskell_var_name(node.id)

        elif isinstance(node, ast.BinOp):
            return self._convert_binary_operation(node)

        elif isinstance(node, ast.UnaryOp):
            return self._convert_unary_operation(node)

        elif isinstance(node, ast.Compare):
            return self._convert_comparison(node)

        elif isinstance(node, ast.BoolOp):
            return self._convert_bool_operation(node)

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
            raise UnsupportedFeatureError(f"Unsupported expression type: {type(node).__name__}")

    def _convert_constant(self, node: ast.Constant) -> str:
        """Convert Python constant to Haskell."""
        if isinstance(node.value, bool):
            return "True" if node.value else "False"
        elif isinstance(node.value, int):
            return str(node.value)
        elif isinstance(node.value, float):
            return str(node.value)
        elif isinstance(node.value, str):
            return f'"{node.value}"'
        elif node.value is None:
            return "()"
        else:
            return str(node.value)

    def _convert_binary_operation(self, node: ast.BinOp) -> str:
        """Convert Python binary operation to Haskell."""
        left = self._convert_expression(node.left)
        right = self._convert_expression(node.right)

        # Handle Haskell-specific operators
        if isinstance(node.op, ast.FloorDiv):
            return f"({left} `div` {right})"
        elif isinstance(node.op, ast.Mod):
            return f"({left} `mod` {right})"
        elif isinstance(node.op, ast.Pow):
            return f"({left} ** {right})"
        elif isinstance(node.op, ast.BitOr):
            return f"({left} .|. {right})"
        elif isinstance(node.op, ast.BitXor):
            return f"({left} `xor` {right})"
        elif isinstance(node.op, ast.BitAnd):
            return f"({left} .&. {right})"
        elif isinstance(node.op, ast.LShift):
            return f"({left} `shiftL` {right})"
        elif isinstance(node.op, ast.RShift):
            return f"({left} `shiftR` {right})"

        # Use standard operator mapping from converter_utils for common operators
        op = get_standard_binary_operator(node.op)
        if op is not None:
            return f"({left} {op} {right})"
        else:
            raise UnsupportedFeatureError(f"Unsupported binary operator: {type(node.op).__name__}")

    def _convert_unary_operation(self, node: ast.UnaryOp) -> str:
        """Convert Python unary operation to Haskell."""
        operand = self._convert_expression(node.operand)

        if isinstance(node.op, ast.UAdd):
            return f"(+{operand})"
        elif isinstance(node.op, ast.USub):
            return f"(-{operand})"
        elif isinstance(node.op, ast.Not):
            return f"(not {operand})"
        elif isinstance(node.op, ast.Invert):
            return f"(complement {operand})"
        else:
            raise UnsupportedFeatureError(f"Unsupported unary operator: {type(node.op).__name__}")

    def _convert_comparison(self, node: ast.Compare) -> str:
        """Convert Python comparison to Haskell."""
        left = self._convert_expression(node.left)

        if len(node.ops) == 1 and len(node.comparators) == 1:
            op = node.ops[0]
            right = self._convert_expression(node.comparators[0])

            # Handle Haskell-specific operators
            if isinstance(op, ast.NotEq):
                # Haskell uses /= for inequality
                return f"({left} /= {right})"
            elif isinstance(op, ast.In):
                # Use Data.Map.member for maps (assuming right is a map)
                return f"(Data.Map.member {left} {right})"
            elif isinstance(op, ast.NotIn):
                # Use not . Data.Map.member for maps
                return f"(not (Data.Map.member {left} {right}))"

            # Use standard comparison operator mapping from converter_utils
            haskell_op = get_standard_comparison_operator(op)
            if haskell_op is not None:
                return f"({left} {haskell_op} {right})"
            else:
                raise UnsupportedFeatureError(f"Unsupported comparison operator: {type(op).__name__}")
        else:
            raise UnsupportedFeatureError("Complex comparison chains not supported")

    def _convert_bool_operation(self, node: ast.BoolOp) -> str:
        """Convert Python boolean operation to Haskell."""
        values = [self._convert_expression(value) for value in node.values]

        if isinstance(node.op, ast.And):
            return "(" + " && ".join(values) + ")"
        elif isinstance(node.op, ast.Or):
            return "(" + " || ".join(values) + ")"
        else:
            raise UnsupportedFeatureError(f"Unsupported boolean operator: {type(node.op).__name__}")

    def _convert_function_call(self, node: ast.Call) -> str:
        """Convert Python function call to Haskell."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            args = [self._convert_expression(arg) for arg in node.args]

            # Handle built-in functions
            if func_name == "print":
                if args:
                    return f"printValue {args[0]}"
                else:
                    return 'printValue ""'
            elif func_name == "len":
                if args:
                    return f"len' {args[0]}"
                else:
                    return "0"  # Default len value
            elif func_name == "abs":
                if args:
                    return f"abs' {args[0]}"
                else:
                    return "abs' 0"  # Default abs value
            elif func_name == "min":
                if args:
                    return f"min' {args[0]}"
                else:
                    return "0"  # Default min value
            elif func_name == "max":
                if args:
                    return f"max' {args[0]}"
                else:
                    return "0"  # Default max value
            elif func_name == "sum":
                if args:
                    return f"sum' {args[0]}"
                else:
                    return "0"  # Default sum value
            elif func_name == "bool":
                if args:
                    return f"bool' {args[0]}"
                else:
                    return "False"  # Default bool value
            elif func_name == "str":
                if args:
                    return f"toString {args[0]}"
                else:
                    return 'toString ""'  # Empty string conversion
            elif func_name == "range":
                if len(args) == 1:
                    return f"rangeList (range {args[0]})"
                elif len(args) == 2:
                    return f"rangeList (range2 {args[0]} {args[1]})"
                elif len(args) == 3:
                    return f"rangeList (range3 {args[0]} {args[1]} {args[2]})"
                else:
                    return "rangeList (range 0)"  # Fallback for invalid range args
            else:
                # Check if it's a class constructor call
                camel_func_name = self._to_camel_case(func_name)
                if camel_func_name in self.data_types:
                    constructor_name = f"new{camel_func_name}"
                    if args:
                        return f"{constructor_name} " + " ".join(args)
                    else:
                        return constructor_name
                else:
                    # Regular function call
                    haskell_func_name = self._to_haskell_function_name(func_name)
                    if args:
                        return f"{haskell_func_name} " + " ".join(args)
                    else:
                        return haskell_func_name

        elif isinstance(node.func, ast.Attribute):
            return self._convert_method_call(node)

        else:
            raise UnsupportedFeatureError("Complex function calls not supported")

    def _convert_method_call(self, node: ast.Call) -> str:
        """Convert Python method call to Haskell function call."""
        if isinstance(node.func, ast.Attribute):
            obj = self._convert_expression(node.func.value)
            method_name = node.func.attr
            args = [self._convert_expression(arg) for arg in node.args]

            # Handle string methods - use qualified names to avoid shadowing
            if method_name == "upper":
                return f"(MGenRuntime.upper {obj})"
            elif method_name == "lower":
                return f"(MGenRuntime.lower {obj})"
            elif method_name == "strip":
                return f"(MGenRuntime.strip {obj})"
            elif method_name == "find":
                if args:
                    return f"(MGenRuntime.find {obj} {args[0]})"
            elif method_name == "replace":
                if len(args) >= 2:
                    return f"(MGenRuntime.replace {obj} {args[0]} {args[1]})"
            elif method_name == "split":
                if args:
                    return f"(MGenRuntime.split {obj} {args[0]})"
            else:
                # Regular method call - convert to function call
                haskell_method_name = self._to_haskell_function_name(method_name)
                all_args = [obj] + args
                return f"({haskell_method_name} " + " ".join(all_args) + ")"

        raise UnsupportedFeatureError("Complex method calls not supported")

    def _convert_attribute_access(self, node: ast.Attribute) -> str:
        """Convert Python attribute access to Haskell record access."""
        obj = self._convert_expression(node.value)
        attr_name = self._to_haskell_var_name(node.attr)
        return f"({attr_name} {obj})"

    def _convert_subscript(self, node: ast.Subscript) -> str:
        """Convert Python subscript to Haskell list/map access."""
        obj = self._convert_expression(node.value)
        index = self._convert_expression(node.slice)

        # For lists: obj !! index
        # For maps: obj Map.! index
        return f"({obj} !! {index})"  # Assuming list access for now

    def _convert_list_literal(self, node: ast.List) -> str:
        """Convert Python list literal to Haskell list."""
        elements = [self._convert_expression(elt) for elt in node.elts]
        return "[" + ", ".join(elements) + "]"

    def _convert_dict_literal(self, node: ast.Dict) -> str:
        """Convert Python dict literal to Haskell Map."""
        pairs = []
        for key, value in zip(node.keys, node.values):
            key_expr = self._convert_expression(key) if key is not None else "undefined"
            value_expr = self._convert_expression(value) if value is not None else "undefined"
            pairs.append(f"({key_expr}, {value_expr})")

        return f"Map.fromList [{', '.join(pairs)}]"

    def _convert_set_literal(self, node: ast.Set) -> str:
        """Convert Python set literal to Haskell Set."""
        elements = [self._convert_expression(elt) for elt in node.elts]
        return f"Set.fromList [{', '.join(elements)}]"

    def _convert_list_comprehension(self, node: ast.ListComp) -> str:
        """Convert Python list comprehension to Haskell."""
        # Check preferences for comprehension style
        use_native = False
        if self.preferences and self.preferences.get("use_native_comprehensions", False):
            use_native = True

        expr = self._convert_expression(node.elt)

        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in comprehensions not supported")

        gen = node.generators[0]
        target = self._to_haskell_var_name(gen.target.id) if isinstance(gen.target, ast.Name) else "x"
        iterable = self._convert_expression(gen.iter)

        if use_native:
            # Use native Haskell list comprehension syntax
            if gen.ifs:
                conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
                condition = " && ".join(conditions)
                return f"[{expr} | {target} <- {iterable}, {condition}]"
            else:
                return f"[{expr} | {target} <- {iterable}]"
        else:
            # Use runtime library functions (default for consistency)
            if gen.ifs:
                conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
                condition = " && ".join(conditions)
                return f"listComprehensionWithFilter {iterable} (\\{target} -> {condition}) (\\{target} -> {expr})"
            else:
                return f"listComprehension {iterable} (\\{target} -> {expr})"

    def _convert_dict_comprehension(self, node: ast.DictComp) -> str:
        """Convert Python dict comprehension to Haskell."""
        # Check preferences for comprehension style
        use_native = False
        if self.preferences and self.preferences.get("use_native_comprehensions", False):
            use_native = True

        key_expr = self._convert_expression(node.key)
        value_expr = self._convert_expression(node.value)

        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in comprehensions not supported")

        gen = node.generators[0]
        target = self._to_haskell_var_name(gen.target.id) if isinstance(gen.target, ast.Name) else "x"
        iterable = self._convert_expression(gen.iter)

        if use_native:
            # Use native Haskell with Map.fromList
            if gen.ifs:
                conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
                condition = " && ".join(conditions)
                return f"Map.fromList [({key_expr}, {value_expr}) | {target} <- {iterable}, {condition}]"
            else:
                return f"Map.fromList [({key_expr}, {value_expr}) | {target} <- {iterable}]"
        else:
            # Use runtime library functions (default for consistency)
            if gen.ifs:
                conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
                condition = " && ".join(conditions)
                return f"dictComprehensionWithFilter {iterable} (\\{target} -> {condition}) (\\{target} -> {key_expr}) (\\{target} -> {value_expr})"
            else:
                return f"dictComprehension {iterable} (\\{target} -> {key_expr}) (\\{target} -> {value_expr})"

    def _convert_set_comprehension(self, node: ast.SetComp) -> str:
        """Convert Python set comprehension to Haskell."""
        # Check preferences for comprehension style
        use_native = False
        if self.preferences and self.preferences.get("use_native_comprehensions", False):
            use_native = True

        expr = self._convert_expression(node.elt)

        if len(node.generators) != 1:
            raise UnsupportedFeatureError("Multiple generators in comprehensions not supported")

        gen = node.generators[0]
        target = self._to_haskell_var_name(gen.target.id) if isinstance(gen.target, ast.Name) else "x"
        iterable = self._convert_expression(gen.iter)

        if use_native:
            # Use native Haskell with Set.fromList
            if gen.ifs:
                conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
                condition = " && ".join(conditions)
                return f"Set.fromList [{expr} | {target} <- {iterable}, {condition}]"
            else:
                return f"Set.fromList [{expr} | {target} <- {iterable}]"
        else:
            # Use runtime library functions (default for consistency)
            if gen.ifs:
                conditions = [self._convert_expression(if_clause) for if_clause in gen.ifs]
                condition = " && ".join(conditions)
                return f"setComprehensionWithFilter {iterable} (\\{target} -> {condition}) (\\{target} -> {expr})"
            else:
                return f"setComprehension {iterable} (\\{target} -> {expr})"

    def _convert_ternary_expression(self, node: ast.IfExp) -> str:
        """Convert Python ternary expression to Haskell if-then-else."""
        test = self._convert_expression(node.test)
        body = self._convert_expression(node.body)
        orelse = self._convert_expression(node.orelse)
        return f"(if {test} then {body} else {orelse})"

    def _convert_operator(self, op_node: ast.operator) -> str:
        """Convert AST operator to Haskell operator string."""
        if isinstance(op_node, ast.FloorDiv):
            return "`div`"
        elif isinstance(op_node, ast.Mod):
            return "`mod`"
        elif isinstance(op_node, ast.Pow):
            return "**"
        elif isinstance(op_node, ast.BitOr):
            return ".|."
        elif isinstance(op_node, ast.BitXor):
            return "`xor`"
        elif isinstance(op_node, ast.BitAnd):
            return ".&."
        elif isinstance(op_node, ast.LShift):
            return "`shiftL`"
        elif isinstance(op_node, ast.RShift):
            return "`shiftR`"
        else:
            # Use standard operator mapping from converter_utils for common operators
            op_result = get_standard_binary_operator(op_node)
            if op_result is None:
                raise UnsupportedFeatureError(f"Unsupported operator: {type(op_node).__name__}")
            return op_result

    def _convert_augmented_assignment(self, node: ast.AugAssign) -> str:
        """Convert Python augmented assignment to Haskell."""
        target = self._convert_expression(node.target)
        value = self._convert_expression(node.value)
        op = self._convert_operator(node.op)
        return f"{target} = ({target} {op} {value})"

    def _convert_if_statement(self, node: ast.If) -> str:
        """Convert Python if statement to Haskell."""
        condition = self._convert_expression(node.test)

        then_stmts = []
        for stmt in node.body:
            converted = self._convert_statement(stmt)
            if converted:
                then_stmts.append(converted)

        else_stmts = []
        for stmt in node.orelse:
            converted = self._convert_statement(stmt)
            if converted:
                else_stmts.append(converted)

        then_body = " >> ".join(then_stmts) if then_stmts else "()"
        else_body = " >> ".join(else_stmts) if else_stmts else "()"

        if else_stmts:
            return f"if {condition} then {then_body} else {else_body}"
        else:
            return f"if {condition} then {then_body} else ()"

    def _convert_while_statement(self, node: ast.While) -> str:
        """Convert Python while loop to Haskell."""
        # Haskell doesn't have while loops - we'd need to use recursion
        raise UnsupportedFeatureError("While loops not directly supported in Haskell")

    def _convert_for_statement(self, node: ast.For) -> str:
        """Convert Python for loop to Haskell."""
        if isinstance(node.target, ast.Name):
            var_name = self._to_haskell_var_name(node.target.id)
            iterable = self._convert_expression(node.iter)

            # Check if loop body is a single assignment or augmented assignment that updates an outer variable
            # Pattern: for i in range(n): var = expr(i)  ->  foldM for IO context
            # Pattern: for i in range(n): var += expr(i)  ->  foldl for pure context
            if len(node.body) == 1:
                stmt = node.body[0]

                # Handle regular assignment in main (IO context)
                if (self.current_function == "main" and isinstance(stmt, ast.Assign)):
                    if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                        updated_var = self._to_haskell_var_name(stmt.targets[0].id)
                        value_expr = self._convert_expression(stmt.value)
                        # Use foldM to update variable through iterations (shadowing in do notation)
                        return f"{updated_var} <- foldM (\\acc {var_name} -> return ({value_expr})) {updated_var} ({iterable})"

                # Handle augmented assignment (accumulation pattern) - works in both pure and IO
                elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                    var_name_target = self._to_haskell_var_name(stmt.target.id)
                    value_expr = self._convert_expression(stmt.value)
                    op = self._convert_operator(stmt.op)

                    # In pure context (not main), use foldl for accumulation
                    if self.current_function != "main":
                        return f"{var_name_target} = foldl (\\acc {var_name} -> acc {op} ({value_expr})) {var_name_target} ({iterable})"
                    else:
                        # In IO context, still use foldM but with accumulator
                        return f"{var_name_target} <- foldM (\\acc {var_name} -> return (acc {op} ({value_expr}))) {var_name_target} ({iterable})"

            body_stmts = []
            for body_stmt in node.body:
                converted = self._convert_statement(body_stmt)
                if converted:
                    body_stmts.append(converted)

            body = " >> ".join(body_stmts) if body_stmts else "()"

            # Use mapM_ for side effects
            return f"mapM_ (\\{var_name} -> {body}) {iterable}"
        else:
            raise UnsupportedFeatureError("Complex for loop targets not supported")

    def _convert_type_annotation(self, node: ast.expr) -> str:
        """Convert Python type annotation to Haskell type."""
        if isinstance(node, ast.Name):
            python_type = node.id
            if python_type == "None":
                return "()"
            return self.type_map.get(python_type, python_type)
        elif isinstance(node, ast.Constant):
            if node.value is None:
                return "()"
            return str(node.value)
        else:
            return "a"  # Default generic type

    def _infer_type_from_node(self, node: ast.expr) -> str:
        """Infer Haskell type from Python expression node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "Bool"
            elif isinstance(node.value, int):
                return "Int"
            elif isinstance(node.value, float):
                return "Double"
            elif isinstance(node.value, str):
                return "String"
        elif isinstance(node, ast.List):
            return "[a]"
        elif isinstance(node, ast.Dict):
            return "Dict String a"
        elif isinstance(node, ast.Set):
            return "Set a"

        return "a"  # Default generic type

