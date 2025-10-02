"""Enhanced Rust code emitter for MGen with comprehensive Python language support."""

import ast
from typing import Any, Optional

from ..base import AbstractEmitter
from ..converter_utils import (
    get_augmented_assignment_operator,
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


class MGenPythonToRustConverter:
    """Sophisticated Python-to-Rust converter with comprehensive language support."""

    def __init__(self) -> None:
        """Initialize the converter."""
        self.type_map = {
            "int": "i32",
            "float": "f64",
            "bool": "bool",
            "str": "String",
            "list": "Vec<Box<dyn std::any::Any>>",
            "dict": "std::collections::HashMap<String, Box<dyn std::any::Any>>",
            "set": "std::collections::HashSet<Box<dyn std::any::Any>>",
            "void": "()",
            "None": "()",
        }
        self.struct_info: dict[str, dict[str, Any]] = {}  # Track struct definitions for classes
        self.current_function: Optional[str] = None  # Track current function context
        self.declared_vars: set[str] = set()  # Track declared variables in current function

    def _to_snake_case(self, camel_str: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _to_rust_method_name(self, method_name: str) -> str:
        """Convert Python method name to Rust method name (snake_case)."""
        return self._to_snake_case(method_name)

    def convert_code(self, python_code: str) -> str:
        """Convert Python code to Rust."""
        try:
            tree = ast.parse(python_code)
            return self._convert_module(tree)
        except UnsupportedFeatureError:
            # Re-raise UnsupportedFeatureError without wrapping
            raise
        except Exception as e:
            raise TypeMappingError(f"Failed to convert Python code: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to Rust."""
        parts = []

        # Add required imports
        imports = self._collect_required_imports(node)
        for imp in imports:
            parts.append(imp)
        if imports:
            parts.append("")

        # Add runtime library declaration
        parts.append("// Include MGen Rust runtime")
        parts.append("mod mgen_rust_runtime;")
        parts.append("use mgen_rust_runtime::*;")
        parts.append("")

        # Convert classes first (they become struct definitions)
        for item in node.body:
            if isinstance(item, ast.ClassDef):
                struct_def = self._convert_class(item)
                parts.append(struct_def)
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
            main_func = """fn main() {
    print_value("Generated Rust code executed successfully");
}"""
            parts.append("")
            parts.append(main_func)

        return "\n".join(parts)

    def _collect_required_imports(self, node: ast.Module) -> list[str]:
        """Collect required imports based on code features."""
        imports: list[str] = []

        # Check for collections usage
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                if n.func.id == "print":
                    pass  # print is handled by our runtime
            elif isinstance(n, ast.ClassDef):
                # Add HashMap/HashSet imports for class usage
                if "use std::collections::" not in "\n".join(imports):
                    imports.append("use std::collections::{HashMap, HashSet};")

        return imports

    def _convert_class(self, node: ast.ClassDef) -> str:
        """Convert Python class to Rust struct with associated functions."""
        class_name = node.name

        # Find __init__ method and other methods
        init_method = None
        other_methods = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    init_method = item
                else:
                    other_methods.append(item)

        # Generate struct definition
        struct_lines = ["#[derive(Clone)]"]
        struct_lines.append(f"struct {class_name} {{")

        if init_method:
            # Extract fields from __init__ method
            for stmt in init_method.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                            field_name = self._to_snake_case(target.attr)
                            field_type = self._infer_type_from_assignment(stmt)
                            struct_lines.append(f"    {field_name}: {field_type},")
                elif isinstance(stmt, ast.AnnAssign):
                    if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                        field_name = self._to_snake_case(stmt.target.attr)
                        field_type = self._map_type_annotation(stmt.annotation)
                        struct_lines.append(f"    {field_name}: {field_type},")
        else:
            # Empty struct
            struct_lines.append("    _dummy: (),")

        struct_lines.append("}")

        # Store struct info for method generation
        self.struct_info[class_name] = {
            "fields": self._extract_struct_fields(init_method) if init_method else []
        }

        # Generate impl block with constructor and methods
        impl_lines = []
        impl_lines.append(f"impl {class_name} {{")

        # Generate constructor
        if init_method:
            constructor_lines = self._convert_constructor(class_name, init_method)
            impl_lines.extend(constructor_lines)

        # Generate methods
        for method in other_methods:
            method_lines = self._convert_method(class_name, method)
            impl_lines.extend(method_lines)
            impl_lines.append("")

        impl_lines.append("}")

        # Combine all parts
        result_lines = struct_lines + [""] + impl_lines
        return "\n".join(result_lines)

    def _convert_constructor(self, class_name: str, init_method: ast.FunctionDef) -> list[str]:
        """Convert __init__ method to Rust constructor function."""
        lines = []

        # Build parameter list (skip self)
        params = []
        for arg in init_method.args.args[1:]:  # Skip self
            param_type = self._infer_parameter_type(arg, init_method)
            params.append(f"{arg.arg}: {param_type}")

        params_str = ", ".join(params)

        # Generate constructor function
        lines.append(f"    fn new({params_str}) -> Self {{")
        lines.append(f"        {class_name} {{")

        # Generate field initialization
        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        field_name = self._to_snake_case(target.attr)
                        value_expr = self._convert_expression(stmt.value)
                        lines.append(f"            {field_name}: {value_expr},")
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                    field_name = self._to_snake_case(stmt.target.attr)
                    if stmt.value:
                        value_expr = self._convert_expression(stmt.value)
                        lines.append(f"            {field_name}: {value_expr},")

        lines.append("        }")
        lines.append("    }")
        lines.append("")

        return lines

    def _convert_method(self, class_name: str, method: ast.FunctionDef) -> list[str]:
        """Convert Python method to Rust method."""
        lines = []

        # Build parameter list (convert self to &mut self)
        params = []
        if method.args.args:
            if method.args.args[0].arg == "self":
                params.append("&mut self")
                # Add other parameters
                for arg in method.args.args[1:]:
                    param_type = self._infer_parameter_type(arg, method)
                    params.append(f"{arg.arg}: {param_type}")
            else:
                # Static method (no self)
                for arg in method.args.args:
                    param_type = self._infer_parameter_type(arg, method)
                    params.append(f"{arg.arg}: {param_type}")

        params_str = ", ".join(params)

        # Get return type
        return_type = ""
        if method.returns:
            mapped_type = self._map_type_annotation(method.returns)
            if mapped_type and mapped_type != "()":
                return_type = f" -> {mapped_type}"

        # Build method signature
        method_name = self._to_rust_method_name(method.name)
        lines.append(f"    fn {method_name}({params_str}){return_type} {{")

        # Convert method body
        self.current_function = method.name
        body = self._convert_method_statements(method.body, class_name)
        self.current_function = None

        lines.append(body)
        lines.append("    }")

        return lines

    def _convert_method_statements(self, statements: list[ast.stmt], class_name: str) -> str:
        """Convert method statements with class context."""
        converted = []
        for stmt in statements:
            converted.append(self._convert_method_statement(stmt, class_name))
        return "\n".join(converted)

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
            if isinstance(target, ast.Name):
                # Local variable assignment
                statements.append(f"        let mut {target.id} = {value_expr};")
            elif isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    # Instance variable assignment: self.attr = value -> self.attr = value
                    field_name = self._to_snake_case(target.attr)
                    statements.append(f"        self.{field_name} = {value_expr};")
                else:
                    # Regular attribute assignment
                    obj_expr = self._convert_method_expression(target.value, class_name)
                    field_name = self._to_snake_case(target.attr)
                    statements.append(f"        {obj_expr}.{field_name} = {value_expr};")

        return "\n".join(statements)

    def _convert_method_annotated_assignment(self, stmt: ast.AnnAssign, class_name: str) -> str:
        """Convert method annotated assignment with proper handling."""
        if stmt.value:
            value_expr = self._convert_method_expression(stmt.value, class_name)
        else:
            type_name = self._map_type_annotation(stmt.annotation)
            value_expr = self._get_default_value(type_name)

        if isinstance(stmt.target, ast.Name):
            # Local variable with type annotation
            var_type = self._map_type_annotation(stmt.annotation)
            return f"        let mut {stmt.target.id}: {var_type} = {value_expr};"
        elif isinstance(stmt.target, ast.Attribute):
            if isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                # Instance variable: self.attr: type = value -> self.attr = value
                field_name = self._to_snake_case(stmt.target.attr)
                return f"        self.{field_name} = {value_expr};"

        return "        // TODO: Complex annotated assignment"

    def _convert_method_aug_assignment(self, stmt: ast.AugAssign, class_name: str) -> str:
        """Convert method augmented assignment with proper self handling."""
        value_expr = self._convert_method_expression(stmt.value, class_name)

        # Get augmented assignment operator from converter_utils
        op = get_augmented_assignment_operator(stmt.op)
        if op is None:
            # Handle Rust-specific operators
            if isinstance(stmt.op, ast.FloorDiv):
                op = "/="  # Rust integer division is already floor division
            else:
                op = "/*UNKNOWN_OP*/"

        if isinstance(stmt.target, ast.Name):
            return f"        {stmt.target.id} {op} {value_expr};"
        elif isinstance(stmt.target, ast.Attribute):
            if isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                field_name = self._to_snake_case(stmt.target.attr)
                return f"        self.{field_name} {op} {value_expr};"

        return f"        // TODO: Complex augmented assignment {op}"

    def _convert_method_return(self, stmt: ast.Return, class_name: str) -> str:
        """Convert method return statement."""
        if stmt.value:
            value_expr = self._convert_method_expression(stmt.value, class_name)
            return f"        return {value_expr};"
        return "        return ();"

    def _convert_method_if(self, stmt: ast.If, class_name: str) -> str:
        """Convert if statement in method context."""
        condition = self._convert_method_expression(stmt.test, class_name)
        then_body = self._convert_method_statements(stmt.body, class_name)

        result = f"        if {condition} {{\n{then_body}\n        }}"

        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif case
                else_part = self._convert_method_if(stmt.orelse[0], class_name).strip()
                result += f" else {else_part[8:]}"  # Remove leading spaces
            else:
                # else case
                else_body = self._convert_method_statements(stmt.orelse, class_name)
                result += f" else {{\n{else_body}\n        }}"

        return result

    def _convert_method_expression(self, expr: ast.expr, class_name: str) -> str:
        """Convert method expression with class context."""
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                # self.attr -> self.attr
                return f"self.{self._to_snake_case(expr.attr)}"
            else:
                # obj.attr or obj.method()
                obj_expr = self._convert_method_expression(expr.value, class_name)
                return f"{obj_expr}.{self._to_snake_case(expr.attr)}"
        elif isinstance(expr, ast.Call):
            return self._convert_method_call(expr, class_name)
        elif isinstance(expr, ast.BinOp):
            # Handle binary operations with proper self conversion
            left = self._convert_method_expression(expr.left, class_name)
            right = self._convert_method_expression(expr.right, class_name)

            # Handle Rust-specific operators
            if isinstance(expr.op, ast.FloorDiv):
                # Rust integer division is already floor division
                return f"({left} / {right})"

            # Use standard operator mapping from converter_utils
            op = get_standard_binary_operator(expr.op)
            if op is None:
                op = "/*UNKNOWN_OP*/"
            return f"({left} {op} {right})"
        elif isinstance(expr, ast.Compare):
            return self._convert_method_compare(expr, class_name)
        elif isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.Constant):
            return self._convert_constant(expr)
        else:
            return self._convert_expression(expr)

    def _convert_method_call(self, expr: ast.Call, class_name: str) -> str:
        """Convert method calls with class context."""
        if isinstance(expr.func, ast.Attribute):
            if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "self":
                # self.method() -> self.method()
                method_name = self._to_rust_method_name(expr.func.attr)
                args = [self._convert_method_expression(arg, class_name) for arg in expr.args]
                args_str = ", ".join(args)
                return f"self.{method_name}({args_str})"
            else:
                # Handle string methods and other attribute calls
                obj_expr = self._convert_method_expression(expr.func.value, class_name)
                method_name = expr.func.attr
                args = [self._convert_method_expression(arg, class_name) for arg in expr.args]

                # Handle string methods
                if method_name in ["upper", "lower", "strip", "find", "replace", "split"]:
                    if method_name == "upper":
                        return f"StrOps::upper(&{obj_expr})"
                    elif method_name == "lower":
                        return f"StrOps::lower(&{obj_expr})"
                    elif method_name == "strip":
                        if args:
                            return f"StrOps::strip_chars(&{obj_expr}, &{args[0]})"
                        else:
                            return f"StrOps::strip(&{obj_expr})"
                    elif method_name == "find":
                        return f"StrOps::find(&{obj_expr}, &{args[0]})"
                    elif method_name == "replace":
                        return f"StrOps::replace(&{obj_expr}, &{args[0]}, &{args[1]})"
                    elif method_name == "split":
                        if args:
                            return f"StrOps::split_sep(&{obj_expr}, &{args[0]})"
                        else:
                            return f"StrOps::split(&{obj_expr})"

                # Regular method call
                args_str = ", ".join(args)
                return f"{obj_expr}.{self._to_rust_method_name(method_name)}({args_str})"
        else:
            # Handle regular function calls like len() with method context
            if isinstance(expr.func, ast.Name):
                func_name = expr.func.id
                args = [self._convert_method_expression(arg, class_name) for arg in expr.args]

                # Handle built-in functions with method context
                if func_name == "len":
                    if args:
                        return f"Builtins::len_string(&{args[0]})"
                    return "0"
                elif func_name == "abs":
                    return f"Builtins::abs_i32({args[0]})"
                elif func_name == "min":
                    if len(args) >= 2:
                        return f"Builtins::min_i32({args[0]}, {args[1]})"
                    else:
                        return "0"  # Fallback for invalid min args
                elif func_name == "max":
                    if len(args) >= 2:
                        return f"Builtins::max_i32({args[0]}, {args[1]})"
                    else:
                        return "0"  # Fallback for invalid max args
                elif func_name == "sum":
                    return f"Builtins::sum_i32(&{args[0]})"
                elif func_name == "str":
                    return f"to_string({args[0]})"
                elif func_name == "range":
                    if len(args) == 1:
                        return f"new_range({args[0]})"
                    elif len(args) == 2:
                        return f"new_range_with_start({args[0]}, {args[1]})"
                    elif len(args) == 3:
                        return f"new_range_with_step({args[0]}, {args[1]}, {args[2]})"
                    else:
                        return "new_range(0)"  # Fallback for invalid range args
                else:
                    # Check if this is a class constructor
                    if func_name in self.struct_info:
                        args_str = ", ".join(args)
                        return f"{func_name}::new({args_str})"
                    else:
                        args_str = ", ".join(args)
                        return f"{func_name}({args_str})"
            else:
                return self._convert_call(expr)

    def _convert_method_compare(self, expr: ast.Compare, class_name: str) -> str:
        """Convert comparison expressions in method context."""
        left = self._convert_method_expression(expr.left, class_name)
        result = left

        for op, comp in zip(expr.ops, expr.comparators):
            # Use standard comparison operator mapping from converter_utils
            op_str = get_standard_comparison_operator(op)

            # Handle Rust-specific operators
            if op_str is None:
                if isinstance(op, ast.Is):
                    op_str = "=="
                elif isinstance(op, ast.IsNot):
                    op_str = "!="
                else:
                    op_str = "/*UNKNOWN_OP*/"

            comp_expr = self._convert_method_expression(comp, class_name)
            result = f"({result} {op_str} {comp_expr})"

        return result

    def _convert_function(self, node: ast.FunctionDef) -> str:
        """Convert Python function to Rust function."""
        # Build parameter list
        params = []
        for arg in node.args.args:
            param_type = self._infer_parameter_type(arg, node)
            params.append(f"{arg.arg}: {param_type}")

        params_str = ", ".join(params)

        # Get return type
        # Special case: Rust's main function must return () or Result
        if node.name == "main":
            return_type = ""
        elif node.returns:
            mapped_type = self._map_type_annotation(node.returns)
            if mapped_type and mapped_type != "()":
                return_type = f" -> {mapped_type}"
            else:
                return_type = ""
        else:
            # Infer return type from function body if no annotation
            inferred_type = self._infer_return_type(node)
            if inferred_type and inferred_type != "()":
                return_type = f" -> {inferred_type}"
            else:
                return_type = ""

        # Build function signature
        func_signature = f"fn {node.name}({params_str}){return_type}"

        # Convert function body
        self.current_function = node.name
        self.declared_vars = set()  # Reset for new function
        # Add parameters to declared variables
        for arg in node.args.args:
            self.declared_vars.add(arg.arg)
        body = self._convert_statements(node.body)
        self.current_function = None

        return f"{func_signature} {{\n{body}\n}}"

    def _convert_statements(self, statements: list[ast.stmt]) -> str:
        """Convert a list of statements."""
        converted = []
        for stmt in statements:
            converted.append(self._convert_statement(stmt))
        return "\n".join(converted)

    def _convert_statement(self, stmt: ast.stmt) -> str:
        """Convert a Python statement to Rust."""
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
        elif isinstance(stmt, ast.Try):
            raise UnsupportedFeatureError("Exception handling (try/except) is not supported in Rust backend")
        elif isinstance(stmt, ast.With):
            raise UnsupportedFeatureError("Context managers (with statement) are not supported in Rust backend")
        else:
            raise UnsupportedFeatureError(f"Statement type {type(stmt).__name__} is not supported in Rust backend")

    def _convert_return(self, stmt: ast.Return) -> str:
        """Convert return statement."""
        # Special case: in main(), ignore return values
        if self.current_function == "main":
            # Just omit the return statement in main
            return ""

        if stmt.value:
            value_expr = self._convert_expression(stmt.value)
            return f"    return {value_expr};"
        return "    return ();"

    def _convert_assignment(self, stmt: ast.Assign) -> str:
        """Convert assignment statement."""
        value_expr = self._convert_expression(stmt.value)
        statements = []

        for target in stmt.targets:
            if isinstance(target, ast.Name):
                if target.id in self.declared_vars:
                    # Variable already declared, use assignment
                    statements.append(f"    {target.id} = {value_expr};")
                else:
                    # First declaration of variable
                    self.declared_vars.add(target.id)
                    var_type = self._infer_type_from_value(stmt.value)

                    # Use explicit type annotation only for primitive literals (constants)
                    # For constructor calls and expressions, let Rust infer the type
                    if isinstance(stmt.value, ast.Constant):
                        statements.append(f"    let mut {target.id}: {var_type} = {value_expr};")
                    else:
                        statements.append(f"    let mut {target.id} = {value_expr};")

        return "\n".join(statements)

    def _convert_annotated_assignment(self, stmt: ast.AnnAssign) -> str:
        """Convert annotated assignment (type annotation)."""
        if stmt.value:
            value_expr = self._convert_expression(stmt.value)
        else:
            type_name = self._map_type_annotation(stmt.annotation)
            value_expr = self._get_default_value(type_name)

        if isinstance(stmt.target, ast.Name):
            # Local variable with type annotation
            var_type = self._map_type_annotation(stmt.annotation)
            return f"    let mut {stmt.target.id}: {var_type} = {value_expr};"

        return "    // TODO: Complex annotated assignment"

    def _convert_aug_assignment(self, stmt: ast.AugAssign) -> str:
        """Convert augmented assignment."""
        value_expr = self._convert_expression(stmt.value)

        # Get augmented assignment operator from converter_utils
        op = get_augmented_assignment_operator(stmt.op)
        if op is None:
            # Handle Rust-specific operators
            if isinstance(stmt.op, ast.FloorDiv):
                op = "/="  # Rust integer division is already floor division
            else:
                op = "/*UNKNOWN_OP*/"

        if isinstance(stmt.target, ast.Name):
            return f"    {stmt.target.id} {op} {value_expr};"

        return f"    // TODO: Complex augmented assignment {op}"

    def _convert_if(self, stmt: ast.If) -> str:
        """Convert if statement."""
        condition = self._convert_expression(stmt.test)
        then_body = self._convert_statements(stmt.body)

        result = f"    if {condition} {{\n{then_body}\n    }}"

        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif case
                else_part = self._convert_if(stmt.orelse[0]).strip()
                result += f" else {else_part[4:]}"  # Remove leading spaces
            else:
                # else case
                else_body = self._convert_statements(stmt.orelse)
                result += f" else {{\n{else_body}\n    }}"

        return result

    def _convert_while(self, stmt: ast.While) -> str:
        """Convert while loop."""
        condition = self._convert_expression(stmt.test)
        body = self._convert_statements(stmt.body)
        return f"    while {condition} {{\n{body}\n    }}"

    def _convert_for(self, stmt: ast.For) -> str:
        """Convert for loop."""
        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name) and stmt.iter.func.id == "range":
            # Handle range-based for loop
            target = stmt.target.id if isinstance(stmt.target, ast.Name) else "i"

            # Convert range arguments
            range_args = [self._convert_expression(arg) for arg in stmt.iter.args]

            if len(range_args) == 1:
                # range(n) -> for i in 0..n
                loop_expr = f"0..{range_args[0]}"
            elif len(range_args) == 2:
                # range(start, stop) -> for i in start..stop
                loop_expr = f"{range_args[0]}..{range_args[1]}"
            else:
                # range(start, stop, step) -> use step_by
                if len(range_args) >= 3:
                    loop_expr = f"({range_args[0]}..{range_args[1]}).step_by({range_args[2]} as usize)"
                else:
                    loop_expr = f"{range_args[0]}..{range_args[1]}"

            body = self._convert_statements(stmt.body)
            return f"    for {target} in {loop_expr} {{\n{body}\n    }}"
        else:
            # General iteration
            target = stmt.target.id if isinstance(stmt.target, ast.Name) else "item"
            iter_expr = self._convert_expression(stmt.iter)
            body = self._convert_statements(stmt.body)
            return f"    for {target} in {iter_expr} {{\n{body}\n    }}"

    def _convert_expression_statement(self, stmt: ast.Expr) -> str:
        """Convert expression statement."""
        expr = self._convert_expression(stmt.value)
        return f"    {expr};"

    def _convert_expression(self, expr: ast.expr) -> str:
        """Convert Python expression to Rust."""
        if isinstance(expr, ast.Constant):
            return self._convert_constant(expr)
        elif isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.BinOp):
            return self._convert_binop(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._convert_unaryop(expr)
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
        elif isinstance(expr, ast.BoolOp):
            return self._convert_boolop(expr)
        elif isinstance(expr, ast.IfExp):
            return self._convert_ternary(expr)
        elif isinstance(expr, ast.List):
            return self._convert_list_literal(expr)
        elif isinstance(expr, ast.Dict):
            return self._convert_dict_literal(expr)
        elif isinstance(expr, ast.Set):
            return self._convert_set_literal(expr)
        elif isinstance(expr, ast.Subscript):
            return self._convert_subscript(expr)
        elif isinstance(expr, ast.GeneratorExp):
            raise UnsupportedFeatureError("Generator expressions are not supported in Rust backend")
        else:
            raise UnsupportedFeatureError(f"Expression type {type(expr).__name__} is not supported in Rust backend")

    def _convert_constant(self, expr: ast.Constant) -> str:
        """Convert constant values."""
        if isinstance(expr.value, str):
            return f'"{expr.value}".to_string()'
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        elif expr.value is None:
            return "()"
        elif isinstance(expr.value, float):
            # Convert whole floats to ints for cleaner code (1.0 -> 1)
            if expr.value.is_integer():
                return str(int(expr.value))
            return f"{expr.value}"
        else:
            return str(expr.value)

    def _convert_binop(self, expr: ast.BinOp) -> str:
        """Convert binary operations."""
        left = self._convert_expression(expr.left)
        right = self._convert_expression(expr.right)

        # Handle Rust-specific operators
        if isinstance(expr.op, ast.Pow):
            return f"{left}.pow({right} as u32)"
        elif isinstance(expr.op, ast.FloorDiv):
            # Rust integer division is already floor division
            return f"({left} / {right})"

        # Use standard operator mapping from converter_utils
        op = get_standard_binary_operator(expr.op)
        if op is None:
            op = "/*UNKNOWN_OP*/"
        return f"({left} {op} {right})"

    def _convert_unaryop(self, expr: ast.UnaryOp) -> str:
        """Convert unary operations."""
        operand = self._convert_expression(expr.operand)

        if isinstance(expr.op, ast.UAdd):
            return f"+{operand}"
        elif isinstance(expr.op, ast.USub):
            # Add parentheses around negative expressions for clarity
            return f"(-{operand})"
        elif isinstance(expr.op, ast.Not):
            return f"!{operand}"
        elif isinstance(expr.op, ast.Invert):
            return f"!{operand}"

        return f"/*UNKNOWN_UNARY_OP*/{operand}"

    def _convert_compare(self, expr: ast.Compare) -> str:
        """Convert comparison expressions."""
        left = self._convert_expression(expr.left)
        result = left

        for op, comp in zip(expr.ops, expr.comparators):
            # Use standard comparison operator mapping from converter_utils
            op_str = get_standard_comparison_operator(op)

            # Handle Rust-specific operators
            if op_str is None:
                if isinstance(op, ast.Is):
                    op_str = "=="
                elif isinstance(op, ast.IsNot):
                    op_str = "!="
                else:
                    op_str = "/*UNKNOWN_OP*/"

            comp_expr = self._convert_expression(comp)
            result = f"({result} {op_str} {comp_expr})"

        return result

    def _convert_boolop(self, expr: ast.BoolOp) -> str:
        """Convert boolean operations (and, or)."""
        values = [self._convert_expression(val) for val in expr.values]

        if isinstance(expr.op, ast.And):
            # Convert 'a and b' to '(a && b)'
            return f"({' && '.join(values)})"
        elif isinstance(expr.op, ast.Or):
            # Convert 'a or b' to '(a || b)'
            return f"({' || '.join(values)})"
        else:
            raise UnsupportedFeatureError(f"Boolean operator {type(expr.op).__name__} is not supported")

    def _convert_ternary(self, expr: ast.IfExp) -> str:
        """Convert ternary expressions (if-else)."""
        # Convert 'a if condition else b' to 'if condition { a } else { b }'
        condition = self._convert_expression(expr.test)
        true_val = self._convert_expression(expr.body)
        false_val = self._convert_expression(expr.orelse)

        return f"if {condition} {{ {true_val} }} else {{ {false_val} }}"

    def _convert_list_literal(self, expr: ast.List) -> str:
        """Convert list literals."""
        if not expr.elts:
            # Empty list
            return "vec![]"

        elements = [self._convert_expression(elt) for elt in expr.elts]
        return f"vec![{', '.join(elements)}]"

    def _convert_dict_literal(self, expr: ast.Dict) -> str:
        """Convert dictionary literals."""
        if not expr.keys:
            # Empty dictionary
            return "std::collections::HashMap::new()"

        # Convert key-value pairs
        pairs = []
        for key, value in zip(expr.keys, expr.values):
            key_expr = self._convert_expression(key) if key is not None else "None"
            value_expr = self._convert_expression(value) if value is not None else "None"
            pairs.append(f"({key_expr}, {value_expr})")

        # Create HashMap using collect()
        return f"[{', '.join(pairs)}].iter().cloned().collect::<std::collections::HashMap<_, _>>()"

    def _convert_set_literal(self, expr: ast.Set) -> str:
        """Convert set literals."""
        if not expr.elts:
            # Empty set
            return "std::collections::HashSet::new()"

        # Convert elements
        elements = [self._convert_expression(elt) for elt in expr.elts]

        # Create HashSet using collect()
        return f"[{', '.join(elements)}].iter().cloned().collect::<std::collections::HashSet<_>>()"

    def _convert_subscript(self, expr: ast.Subscript) -> str:
        """Convert subscript operations (indexing)."""
        value = self._convert_expression(expr.value)
        slice_expr = self._convert_expression(expr.slice)

        # For now, treat all subscripts as HashMap/dict access with get()
        # This is a simplification - in a full implementation we'd need to
        # distinguish between lists, dicts, etc.
        return f"{value}.get(&{slice_expr}).unwrap().clone()"

    def _convert_call(self, expr: ast.Call) -> str:
        """Convert function calls."""
        if isinstance(expr.func, ast.Name):
            func_name = expr.func.id
            args = [self._convert_expression(arg) for arg in expr.args]

            # Handle built-in functions
            if func_name == "print":
                args_str = ", ".join(args)
                return f"print_value({args_str})"
            elif func_name == "len":
                if args:
                    return f"Builtins::len_string(&{args[0]})"
                return "0"
            elif func_name == "abs":
                return f"Builtins::abs_i32({args[0]})"
            elif func_name == "min":
                if len(args) >= 2:
                    return f"Builtins::min_i32({args[0]}, {args[1]})"
                else:
                    return "0"  # Fallback for invalid min args
            elif func_name == "max":
                if len(args) >= 2:
                    return f"Builtins::max_i32({args[0]}, {args[1]})"
                else:
                    return "0"  # Fallback for invalid max args
            elif func_name == "sum":
                return f"Builtins::sum_i32(&{args[0]})"
            elif func_name == "bool":
                return f"to_bool({args[0]})"
            elif func_name == "int":
                return f"to_i32_from_f64({args[0]})"
            elif func_name == "float":
                return f"to_f64_from_i32({args[0]})"
            elif func_name == "str":
                return f"to_string({args[0]})"
            elif func_name == "range":
                if len(args) == 1:
                    return f"new_range({args[0]}).collect()"
                elif len(args) == 2:
                    return f"new_range_with_start({args[0]}, {args[1]}).collect()"
                elif len(args) == 3:
                    return f"new_range_with_step({args[0]}, {args[1]}, {args[2]}).collect()"
                else:
                    return "new_range(0).collect()"  # Fallback for invalid range args
            else:
                # Check if this is a class constructor
                if func_name in self.struct_info:
                    args_str = ", ".join(args)
                    return f"{func_name}::new({args_str})"
                else:
                    args_str = ", ".join(args)
                    return f"{func_name}({args_str})"

        elif isinstance(expr.func, ast.Attribute):
            return self._convert_method_call_expression(expr)
        else:
            return "/* Complex function call */"

    def _convert_method_call_expression(self, expr: ast.Call) -> str:
        """Convert method calls on objects."""
        if isinstance(expr.func, ast.Attribute):
            obj_expr = self._convert_expression(expr.func.value)
            method_name = expr.func.attr
            args = [self._convert_expression(arg) for arg in expr.args]

            # Handle string methods
            if method_name in ["upper", "lower", "strip", "find", "replace", "split"]:
                if method_name == "upper":
                    return f"StrOps::upper(&{obj_expr})"
                elif method_name == "lower":
                    return f"StrOps::lower(&{obj_expr})"
                elif method_name == "strip":
                    if args:
                        return f"StrOps::strip_chars(&{obj_expr}, &{args[0]})"
                    else:
                        return f"StrOps::strip(&{obj_expr})"
                elif method_name == "find":
                    return f"StrOps::find(&{obj_expr}, &{args[0]})"
                elif method_name == "replace":
                    return f"StrOps::replace(&{obj_expr}, &{args[0]}, &{args[1]})"
                elif method_name == "split":
                    if args:
                        return f"StrOps::split_sep(&{obj_expr}, &{args[0]})"
                    else:
                        return f"StrOps::split(&{obj_expr})"

            # Regular method call
            args_str = ", ".join(args)
            return f"{obj_expr}.{self._to_rust_method_name(method_name)}({args_str})"

        return "/* Complex method call */"

    def _convert_attribute(self, expr: ast.Attribute) -> str:
        """Convert attribute access."""
        obj_expr = self._convert_expression(expr.value)
        return f"{obj_expr}.{self._to_snake_case(expr.attr)}"

    def _convert_list_comprehension(self, expr: ast.ListComp) -> str:
        """Convert list comprehensions."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]

            if len(range_args) == 1:
                range_call = f"new_range({range_args[0]}).collect()"
            elif len(range_args) == 2:
                range_call = f"new_range_with_start({range_args[0]}, {range_args[1]}).collect()"
            else:
                range_call = f"new_range_with_step({range_args[0]}, {range_args[1]}, {range_args[2]}).collect()"

            # Create transform closure
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)

            if conditions:
                # With condition
                condition_expr = self._convert_expression(conditions[0])
                return f"Comprehensions::list_comprehension_with_filter({range_call}, |{target_name}| {transform_expr}, |{target_name}| {condition_expr})"
            else:
                # No condition
                return f"Comprehensions::list_comprehension({range_call}, |{target_name}| {transform_expr})"
        else:
            # Container iteration
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)

            if conditions:
                condition_expr = self._convert_expression(conditions[0])
                return f"Comprehensions::list_comprehension_with_filter({container_expr}, |{target_name}| {transform_expr}, |{target_name}| {condition_expr})"
            else:
                return f"Comprehensions::list_comprehension({container_expr}, |{target_name}| {transform_expr})"

    def _convert_dict_comprehension(self, expr: ast.DictComp) -> str:
        """Convert dictionary comprehensions."""
        # Extract comprehension components
        key_expr = expr.key
        value_expr = expr.value
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]

            if len(range_args) == 1:
                range_call = f"new_range({range_args[0]}).collect()"
            elif len(range_args) == 2:
                range_call = f"new_range_with_start({range_args[0]}, {range_args[1]}).collect()"
            else:
                range_call = f"new_range_with_step({range_args[0]}, {range_args[1]}, {range_args[2]}).collect()"

            # Create key-value transform closure
            target_name = target.id if isinstance(target, ast.Name) else "x"
            key_transform = self._convert_expression(key_expr)
            value_transform = self._convert_expression(value_expr)

            if conditions:
                # With condition
                condition_expr = self._convert_expression(conditions[0])
                return f"Comprehensions::dict_comprehension_with_filter({range_call}, |{target_name}| ({key_transform}, {value_transform}), |{target_name}| {condition_expr})"
            else:
                # No condition
                return f"Comprehensions::dict_comprehension({range_call}, |{target_name}| ({key_transform}, {value_transform}))"
        else:
            # Container iteration
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            key_transform = self._convert_expression(key_expr)
            value_transform = self._convert_expression(value_expr)

            if conditions:
                condition_expr = self._convert_expression(conditions[0])
                return f"Comprehensions::dict_comprehension_with_filter({container_expr}, |{target_name}| ({key_transform}, {value_transform}), |{target_name}| {condition_expr})"
            else:
                return f"Comprehensions::dict_comprehension({container_expr}, |{target_name}| ({key_transform}, {value_transform}))"

    def _convert_set_comprehension(self, expr: ast.SetComp) -> str:
        """Convert set comprehensions."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter
        conditions = expr.generators[0].ifs

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            # Range-based comprehension
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]

            if len(range_args) == 1:
                range_call = f"new_range({range_args[0]}).collect()"
            elif len(range_args) == 2:
                range_call = f"new_range_with_start({range_args[0]}, {range_args[1]}).collect()"
            else:
                range_call = f"new_range_with_step({range_args[0]}, {range_args[1]}, {range_args[2]}).collect()"

            # Create transform closure
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)

            if conditions:
                # With condition
                condition_expr = self._convert_expression(conditions[0])
                return f"Comprehensions::set_comprehension_with_filter({range_call}, |{target_name}| {transform_expr}, |{target_name}| {condition_expr})"
            else:
                # No condition
                return f"Comprehensions::set_comprehension({range_call}, |{target_name}| {transform_expr})"
        else:
            # Container iteration
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)

            if conditions:
                condition_expr = self._convert_expression(conditions[0])
                return f"Comprehensions::set_comprehension_with_filter({container_expr}, |{target_name}| {transform_expr}, |{target_name}| {condition_expr})"
            else:
                return f"Comprehensions::set_comprehension({container_expr}, |{target_name}| {transform_expr})"

    # Helper methods for type inference and mapping

    def _map_type_annotation(self, annotation: ast.expr) -> str:
        """Map Python type annotation to Rust type."""
        if isinstance(annotation, ast.Name):
            return self.type_map.get(annotation.id, "i32")
        elif isinstance(annotation, ast.Subscript):
            # Handle subscripted types like list[int], dict[str, int], set[int]
            if isinstance(annotation.value, ast.Name):
                container_type = annotation.value.id
                if container_type == "list":
                    # list[int] -> Vec<i32>
                    if isinstance(annotation.slice, ast.Name):
                        element_type = self.type_map.get(annotation.slice.id, annotation.slice.id)
                        return f"Vec<{element_type}>"
                    return "Vec<i32>"  # Default to Vec<i32>
                elif container_type == "dict":
                    # dict[str, int] -> HashMap<String, i32>
                    if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) == 2:
                        key_type = self._map_type_annotation(annotation.slice.elts[0])
                        value_type = self._map_type_annotation(annotation.slice.elts[1])
                        return f"std::collections::HashMap<{key_type}, {value_type}>"
                    return "std::collections::HashMap<String, i32>"  # Default
                elif container_type == "set":
                    # set[int] -> HashSet<i32>
                    if isinstance(annotation.slice, ast.Name):
                        element_type = self.type_map.get(annotation.slice.id, annotation.slice.id)
                        return f"std::collections::HashSet<{element_type}>"
                    return "std::collections::HashSet<i32>"  # Default
            return "i32"
        elif isinstance(annotation, ast.Constant):
            if annotation.value is None:
                return "()"  # None type should be unit type
            return str(annotation.value)
        else:
            return "i32"

    def _infer_type_from_value(self, value: ast.expr) -> str:
        """Infer Rust type from Python value."""
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):  # Check bool first since bool is subclass of int
                return "bool"
            elif isinstance(value.value, int):
                return "i32"
            elif isinstance(value.value, float):
                return "f64"
            elif isinstance(value.value, str):
                return "String"
        elif isinstance(value, ast.List):
            # Infer type from list literal elements
            if value.elts:
                element_types = [self._infer_type_from_value(elt) for elt in value.elts]
                # If all elements have the same type, use it
                if element_types and all(t == element_types[0] for t in element_types):
                    return f"Vec<{element_types[0]}>"
            return "Vec<i32>"  # Default
        elif isinstance(value, ast.Dict):
            # Infer type from dict literal keys and values
            if value.keys and value.values:
                key_types = [self._infer_type_from_value(key) for key in value.keys if key]
                value_types = [self._infer_type_from_value(val) for val in value.values if val]
                if (key_types and all(t == key_types[0] for t in key_types) and
                    value_types and all(t == value_types[0] for t in value_types)):
                    return f"std::collections::HashMap<{key_types[0]}, {value_types[0]}>"
            return "std::collections::HashMap<String, i32>"  # Default
        elif isinstance(value, ast.Set):
            # Infer type from set literal elements
            if value.elts:
                element_types = [self._infer_type_from_value(elt) for elt in value.elts]
                if element_types and all(t == element_types[0] for t in element_types):
                    return f"std::collections::HashSet<{element_types[0]}>"
            return "std::collections::HashSet<i32>"  # Default
        elif isinstance(value, ast.ListComp):
            # Infer type from list comprehension element
            element_type = self._infer_comprehension_element_type(value.elt)
            return f"Vec<{element_type}>"
        elif isinstance(value, ast.DictComp):
            # Infer type from dict comprehension key and value
            key_type = self._infer_comprehension_element_type(value.key)
            value_type = self._infer_comprehension_element_type(value.value)
            return f"std::collections::HashMap<{key_type}, {value_type}>"
        elif isinstance(value, ast.SetComp):
            # Infer type from set comprehension element
            element_type = self._infer_comprehension_element_type(value.elt)
            return f"std::collections::HashSet<{element_type}>"
        elif isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name):
                func_name = value.func.id
                if func_name in self.struct_info:
                    return func_name
                elif func_name == "sum":
                    return "i32"  # sum() returns integer
                elif func_name == "len":
                    return "usize"  # len() returns usize in Rust
                elif func_name == "abs":
                    return "i32"  # Default for abs
                elif func_name == "min" or func_name == "max":
                    return "i32"  # Default for min/max
            elif isinstance(value.func, ast.Attribute):
                # Method call - try to infer from method name
                method_name = value.func.attr
                if method_name in ["upper", "lower", "strip", "replace"]:
                    return "String"
                elif method_name == "find":
                    return "i32"  # Returns index

        return "i32"

    def _infer_comprehension_element_type(self, expr: ast.expr) -> str:
        """Infer the type of elements produced by a comprehension expression."""
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool"
            elif isinstance(expr.value, int):
                return "i32"
            elif isinstance(expr.value, float):
                return "f64"
            elif isinstance(expr.value, str):
                return "String"
        elif isinstance(expr, ast.Name):
            # Variable reference - default to i32
            return "i32"
        elif isinstance(expr, ast.BinOp):
            # For binary operations, try to infer from operands
            left_type = self._infer_comprehension_element_type(expr.left)
            right_type = self._infer_comprehension_element_type(expr.right)
            if left_type == right_type:
                return left_type
            # If mixed int/float, return float
            if {left_type, right_type} == {"i32", "f64"}:
                return "f64"
            return "i32"
        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                func_name = expr.func.id
                if func_name == "str":
                    return "String"
                elif func_name in ["abs", "sum", "len", "min", "max"]:
                    return "i32"
            elif isinstance(expr.func, ast.Attribute):
                method_name = expr.func.attr
                if method_name in ["upper", "lower", "strip", "replace"]:
                    return "String"

        return "i32"  # Default to i32

    def _infer_type_from_assignment(self, stmt: ast.Assign) -> str:
        """Infer type from assignment statement."""
        return self._infer_type_from_value(stmt.value)

    def _infer_parameter_type(self, arg: ast.arg, func: ast.FunctionDef) -> str:
        """Infer parameter type from annotation or context."""
        if arg.annotation:
            return self._map_type_annotation(arg.annotation)
        return "i32"

    def _infer_return_type(self, func: ast.FunctionDef) -> str:
        """Infer return type from function body."""
        for stmt in func.body:
            if isinstance(stmt, ast.Return) and stmt.value:
                # Found return statement, infer type
                return "i32"  # Default to i32 for complex expressions
        return "()"  # No return statement found

    def _is_constructor_call(self, value: ast.expr) -> bool:
        """Check if the expression is a constructor call."""
        return (isinstance(value, ast.Call) and
                isinstance(value.func, ast.Name) and
                value.func.id in self.struct_info)

    def _extract_struct_fields(self, init_method: ast.FunctionDef) -> list[str]:
        """Extract struct field names from __init__ method."""
        fields = []
        for stmt in init_method.body:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                if isinstance(stmt.target if hasattr(stmt, "target") else stmt.targets[0], ast.Attribute):
                    target = stmt.target if hasattr(stmt, "target") else stmt.targets[0]
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        fields.append(target.attr)
        return fields

    def _get_default_value(self, rust_type: str) -> str:
        """Get default value for Rust type."""
        defaults = {
            "i32": "0",
            "i64": "0",
            "u32": "0",
            "u64": "0",
            "usize": "0",
            "f32": "0.0",
            "f64": "0.0",
            "bool": "false",
            "String": '"".to_string()',
            "()": "()",
        }

        # Handle specific defaults
        if rust_type in defaults:
            return defaults[rust_type]

        # Handle Vec<T> types
        if rust_type.startswith("Vec<"):
            return "Vec::new()"

        # Handle HashMap<K, V> types
        if rust_type.startswith("std::collections::HashMap<"):
            return "std::collections::HashMap::new()"

        # Handle HashSet<T> types
        if rust_type.startswith("std::collections::HashSet<"):
            return "std::collections::HashSet::new()"

        # Default fallback
        return "Default::default()"


class RustEmitter(AbstractEmitter):
    """Enhanced Rust code emitter using the MGenPythonToRustConverter."""

    def __init__(self, preferences: Optional[BackendPreferences] = None) -> None:
        """Initialize Rust emitter."""
        super().__init__(preferences)
        self.converter = MGenPythonToRustConverter()

    def map_python_type(self, python_type: str) -> str:
        """Map Python type to Rust type."""
        return self.converter.type_map.get(python_type, "i32")

    def emit_function(self, func_node: ast.FunctionDef, type_context: dict[str, str]) -> str:
        """Generate Rust function code using converter."""
        # Create a simple module with just this function
        module = ast.Module(body=[func_node], type_ignores=[])
        full_code = self.converter._convert_module(module)

        # Extract just the function part (remove imports and main)
        lines = full_code.split("\n")
        function_lines = []
        in_function = False
        brace_count = 0

        for line in lines:
            if line.strip().startswith(f"fn {func_node.name}("):
                in_function = True
                function_lines.append(line)
                if "{" in line:
                    brace_count += line.count("{") - line.count("}")
            elif in_function:
                function_lines.append(line)
                if "{" in line or "}" in line:
                    brace_count += line.count("{") - line.count("}")
                    if brace_count == 0:
                        break

        return "\n".join(function_lines)

    def emit_module(self, source_code: str, analysis_result: Any) -> str:
        """Generate complete Rust module using converter."""
        return self.converter.convert_code(source_code)

    def can_use_simple_emission(self, func_node: ast.FunctionDef, type_context: dict[str, str]) -> bool:
        """Check if function can use simple emission strategy."""
        # Use the advanced converter for all functions
        return False
