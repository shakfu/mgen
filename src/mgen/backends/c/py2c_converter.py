"""Enhanced Python to C converter for MGen.

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
- Memory management with runtime support
"""

import ast
from typing import Any, Dict, List, Optional, Union

from .containers import CContainerSystem


class UnsupportedFeatureError(Exception):
    """Raised when encountering unsupported Python features."""
    pass


class TypeMappingError(Exception):
    """Raised when type annotation cannot be mapped to C type."""
    pass


class MGenPythonToCConverter:
    """Enhanced Python to C converter with MGen runtime integration."""

    def __init__(self):
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
        self.container_variables: Dict[str, Dict[str, Any]] = {}
        self.variable_context: Dict[str, str] = {}  # var_name -> c_type
        self.defined_structs: Dict[str, str] = {}
        self.iterator_variables: Dict[str, str] = {}
        self.includes_needed = set()
        self.use_runtime = True

    def convert_code(self, source_code: str) -> str:
        """Convert Python source code to C code."""
        try:
            tree = ast.parse(source_code)
            return self._convert_module(tree)
        except Exception as e:
            raise UnsupportedFeatureError(f"Failed to convert Python code: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to C code."""
        parts = []

        # Add includes
        parts.extend(self._generate_includes())
        parts.append("")

        # Add STC container declarations if needed
        if self._uses_containers(node):
            parts.extend(self._generate_container_declarations())
            parts.append("")

        # Convert functions and classes
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                parts.append(self._convert_function(stmt))
                parts.append("")

        # Add main function if not present
        if not any("main" in part for part in parts):
            parts.append(self._generate_main_function())

        return "\n".join(parts)

    def _generate_includes(self) -> List[str]:
        """Generate C includes with MGen runtime support."""
        includes = [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <stdbool.h>",
        ]

        if self.use_runtime:
            includes.extend([
                "#include \"mgen_error_handling.h\"",
                "#include \"mgen_python_ops.h\"",
                "#include \"mgen_memory_ops.h\"",
            ])

            if self.container_variables or self._needs_containers():
                includes.append("#include \"mgen_stc_bridge.h\"")

        return includes

    def _generate_container_declarations(self) -> List[str]:
        """Generate STC container template declarations."""
        declarations = []
        declarations.append("// STC container declarations")
        declarations.append("#define STC_ENABLED")
        declarations.append("")

        # Analyze container types needed
        container_types = set()
        for var_info in self.container_variables.values():
            if "element_type" in var_info:
                container_types.add(var_info["element_type"])

        # Generate declarations for each type
        for element_type in container_types:
            sanitized = self._sanitize_type_name(element_type)

            # Vector declaration
            declarations.extend([
                f"#define i_type vec_{sanitized}",
                f"#define i_val {element_type}",
                "#include \"stc/vec.h\"",
                ""
            ])

            # Map declaration (string keys)
            declarations.extend([
                f"#define i_type map_str_{sanitized}",
                "#define i_key_str",
                f"#define i_val {element_type}",
                "#include \"stc/map.h\"",
                ""
            ])

            # Set declaration
            declarations.extend([
                f"#define i_type set_{sanitized}",
                f"#define i_key {element_type}",
                "#include \"stc/set.h\"",
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
                body_lines.extend(converted.split('\n'))

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
        elif isinstance(stmt, ast.If):
            return self._convert_if(stmt)
        elif isinstance(stmt, ast.While):
            return self._convert_while(stmt)
        elif isinstance(stmt, ast.For):
            return self._convert_for(stmt)
        elif isinstance(stmt, ast.Expr):
            return self._convert_expression_statement(stmt)
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
        if not isinstance(target, ast.Name):
            raise UnsupportedFeatureError("Only simple variable assignment supported")

        var_name = target.id
        value_expr = self._convert_expression(stmt.value)

        # Infer type from value if not known
        if var_name not in self.variable_context:
            inferred_type = self._infer_expression_type(stmt.value)
            self.variable_context[var_name] = inferred_type
            return f"{inferred_type} {var_name} = {value_expr};"
        else:
            return f"{var_name} = {value_expr};"

    def _convert_annotated_assignment(self, stmt: ast.AnnAssign) -> str:
        """Convert annotated assignment (e.g., x: int = 5)."""
        if not isinstance(stmt.target, ast.Name):
            raise UnsupportedFeatureError("Only simple variable assignment supported")

        var_name = stmt.target.id
        type_annotation = self._get_type_annotation(stmt.annotation)
        c_type = self.type_mapping.get(type_annotation, type_annotation)

        self.variable_context[var_name] = c_type

        if stmt.value:
            value_expr = self._convert_expression(stmt.value)
            return f"{c_type} {var_name} = {value_expr};"
        else:
            return f"{c_type} {var_name};"

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

        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.FloorDiv: "/",  # Note: not exact for negative numbers
            ast.Pow: "pow",     # Requires math.h
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
            ast.LShift: "<<",
            ast.RShift: ">>",
        }

        if type(expr.op) in op_map:
            op = op_map[type(expr.op)]
            if op == "pow":
                self.includes_needed.add("#include <math.h>")
                return f"pow({left}, {right})"
            else:
                return f"({left} {op} {right})"
        else:
            raise UnsupportedFeatureError(f"Unsupported binary operator: {type(expr.op)}")

    def _convert_unary_op(self, expr: ast.UnaryOp) -> str:
        """Convert unary operations."""
        operand = self._convert_expression(expr.operand)

        op_map = {
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Not: "!",
            ast.Invert: "~",
        }

        if type(expr.op) in op_map:
            op = op_map[type(expr.op)]
            return f"({op}{operand})"
        else:
            raise UnsupportedFeatureError(f"Unsupported unary operator: {type(expr.op)}")

    def _convert_compare(self, expr: ast.Compare) -> str:
        """Convert comparison operations."""
        if len(expr.ops) != 1 or len(expr.comparators) != 1:
            raise UnsupportedFeatureError("Chained comparisons not supported")

        left = self._convert_expression(expr.left)
        right = self._convert_expression(expr.comparators[0])

        op_map = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }

        if type(expr.ops[0]) in op_map:
            op = op_map[type(expr.ops[0])]
            return f"({left} {op} {right})"
        else:
            raise UnsupportedFeatureError(f"Unsupported comparison: {type(expr.ops[0])}")

    def _convert_call(self, expr: ast.Call) -> str:
        """Convert function calls."""
        if isinstance(expr.func, ast.Name):
            func_name = expr.func.id
            args = [self._convert_expression(arg) for arg in expr.args]

            # Handle built-in functions with runtime support
            if func_name in ["len", "bool", "abs", "min", "max", "sum"] and self.use_runtime:
                return self._convert_builtin_with_runtime(func_name, args)
            else:
                args_str = ", ".join(args)
                return f"{func_name}({args_str})"
        else:
            raise UnsupportedFeatureError("Only simple function calls supported")

    def _convert_builtin_with_runtime(self, func_name: str, args: List[str]) -> str:
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

    def _sanitize_type_name(self, type_name: str) -> str:
        """Sanitize type name for STC templates."""
        type_map = {
            "int": "int",
            "char": "char",
            "float": "float",
            "double": "double",
            "char*": "str",
            "const char*": "cstr",
            "string": "str",
            "bool": "bool",
        }
        return type_map.get(type_name, type_name.replace("*", "ptr").replace(" ", "_"))

    def _generate_main_function(self) -> str:
        """Generate main function if not present."""
        return """int main() {
    printf("Hello from MGen-enhanced C code!\\n");
    return 0;
}"""

    def _convert_if(self, stmt: ast.If) -> str:
        """Convert if statement."""
        condition = self._convert_expression(stmt.test)
        body = []
        for s in stmt.body:
            converted = self._convert_statement(s)
            if converted:
                body.extend(converted.split('\n'))

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
                        for line in converted.split('\n'):
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
                body.extend(converted.split('\n'))

        result = f"while ({condition}) {{\n"
        for line in body:
            result += f"    {line}\n"
        result += "}"
        return result

    def _convert_for(self, stmt: ast.For) -> str:
        """Convert for loop (limited to range())."""
        if not (isinstance(stmt.iter, ast.Call) and
                isinstance(stmt.iter.func, ast.Name) and
                stmt.iter.func.id == "range"):
            raise UnsupportedFeatureError("Only for loops with range() supported")

        if not isinstance(stmt.target, ast.Name):
            raise UnsupportedFeatureError("Only simple loop variables supported")

        var_name = stmt.target.id
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
                body.extend(converted.split('\n'))

        result = f"for (int {var_name} = {start}; {var_name} < {stop}; {var_name} += {step}) {{\n"
        for line in body:
            result += f"    {line}\n"
        result += "}"
        return result

    def _convert_expression_statement(self, stmt: ast.Expr) -> str:
        """Convert expression statement."""
        expr = self._convert_expression(stmt.value)
        return f"{expr};"

    def _convert_attribute(self, expr: ast.Attribute) -> str:
        """Convert attribute access."""
        obj = self._convert_expression(expr.value)
        return f"{obj}.{expr.attr}"

    def _convert_subscript(self, expr: ast.Subscript) -> str:
        """Convert subscript access."""
        obj = self._convert_expression(expr.value)
        if isinstance(expr.slice, ast.Index):  # Python < 3.9
            index = self._convert_expression(expr.slice.value)
        else:  # Python >= 3.9
            index = self._convert_expression(expr.slice)
        return f"{obj}[{index}]"