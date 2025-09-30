"""Enhanced Go code emitter for MGen with comprehensive Python language support."""

import ast
from typing import Any, Optional, Union

from ..base import AbstractEmitter
from ..preferences import BackendPreferences


class UnsupportedFeatureError(Exception):
    """Raised when encountering unsupported Python features."""
    pass


class TypeMappingError(Exception):
    """Raised when type mapping fails."""
    pass


class MGenPythonToGoConverter:
    """Sophisticated Python-to-Go converter with comprehensive language support."""

    def __init__(self) -> None:
        """Initialize the converter."""
        self.type_map = {
            "int": "int",
            "float": "float64",
            "bool": "bool",
            "str": "string",
            "list": "[]interface{}",
            "dict": "map[interface{}]interface{}",
            "set": "map[interface{}]bool",
            "void": "",
            "None": "",
        }
        self.struct_info: dict[str, dict[str, Any]] = {}  # Track struct definitions for classes
        self.current_function: Optional[str] = None  # Track current function context
        self.declared_vars: set[str] = set()  # Track declared variables in current function

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to CamelCase."""
        components = snake_str.split("_")
        return "".join(word.capitalize() for word in components)

    def _to_go_method_name(self, method_name: str) -> str:
        """Convert Python method name to Go method name (proper CamelCase)."""
        # Handle special cases like get_increment -> GetIncrement
        return self._to_camel_case(method_name)

    def convert_code(self, python_code: str) -> str:
        """Convert Python code to Go."""
        try:
            tree = ast.parse(python_code)
            return self._convert_module(tree)
        except Exception as e:
            raise TypeMappingError(f"Failed to convert Python code: {e}")

    def _convert_module(self, node: ast.Module) -> str:
        """Convert a Python module to Go."""
        parts = []

        # Package declaration
        parts.append("package main")
        parts.append("")

        # Imports
        imports = self._collect_required_imports(node)
        for imp in imports:
            parts.append(f'import "{imp}"')
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
            main_func = 'func main() {\n    mgen.Print("Generated Go code executed successfully")\n}'
            parts.append("")
            parts.append(main_func)

        return "\n".join(parts)

    def _collect_required_imports(self, node: ast.Module) -> list[str]:
        """Collect required imports based on code features."""
        imports = ["mgen"]  # Always import our runtime

        # Check for print usage
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                if n.func.id == "print":
                    if "fmt" not in imports:
                        imports.append("fmt")

        return imports

    def _convert_class(self, node: ast.ClassDef) -> str:
        """Convert Python class to Go struct with methods."""
        class_name = node.name

        # Extract instance variables from __init__ method
        init_method = None
        other_methods = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    init_method = item
                else:
                    other_methods.append(item)

        # Build struct definition
        struct_lines = [f"type {class_name} struct {{"]

        if init_method:
            # Extract instance variables from __init__
            for stmt in init_method.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                            field_name = self._to_camel_case(target.attr)  # Capitalize for Go visibility
                            field_type = self._infer_type_from_assignment(stmt)
                            struct_lines.append(f"    {field_name} {field_type}")
                elif isinstance(stmt, ast.AnnAssign):
                    if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                        field_name = self._to_camel_case(stmt.target.attr)
                        field_type = self._map_type_annotation(stmt.annotation)
                        struct_lines.append(f"    {field_name} {field_type}")

        struct_lines.append("}")

        # Store struct info for method generation
        self.struct_info[class_name] = {
            "fields": self._extract_struct_fields(init_method) if init_method else []
        }

        # Generate constructor
        constructor_lines = []
        if init_method:
            constructor_lines.append(self._convert_constructor(class_name, init_method))

        # Generate methods
        method_lines = []
        for method in other_methods:
            method_lines.append(self._convert_method(class_name, method))

        # Combine all parts
        result_parts = ["\n".join(struct_lines)]
        if constructor_lines:
            result_parts.extend(constructor_lines)
        if method_lines:
            result_parts.extend(method_lines)

        return "\n\n".join(result_parts)

    def _convert_constructor(self, class_name: str, init_method: ast.FunctionDef) -> str:
        """Generate Go constructor function from Python __init__."""
        # Build parameter list (skip 'self')
        params = []
        for arg in init_method.args.args[1:]:  # Skip self
            param_type = self._infer_parameter_type(arg, init_method)
            params.append(f"{arg.arg} {param_type}")

        params_str = ", ".join(params)

        # Generate constructor body
        body_lines = [f"    obj := {class_name}{{}}"]

        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        field_name = self._to_camel_case(target.attr)
                        value_expr = self._convert_expression(stmt.value)
                        body_lines.append(f"    obj.{field_name} = {value_expr}")
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                    field_name = self._to_camel_case(stmt.target.attr)
                    if stmt.value:
                        value_expr = self._convert_expression(stmt.value)
                        body_lines.append(f"    obj.{field_name} = {value_expr}")

        body_lines.append("    return obj")

        # Build function signature
        func_signature = f"func New{class_name}({params_str}) {class_name}"

        return f"{func_signature} {{\n" + "\n".join(body_lines) + "\n}"

    def _convert_method(self, class_name: str, method: ast.FunctionDef) -> str:
        """Convert Python instance method to Go method."""
        # Build parameter list (convert 'self' to receiver)
        params = []
        for arg in method.args.args[1:]:  # Skip self
            param_type = self._infer_parameter_type(arg, method)
            params.append(f"{arg.arg} {param_type}")

        params_str = ", ".join(params)

        # Get return type
        return_type = ""
        if method.returns:
            mapped_type = self._map_type_annotation(method.returns)
            if mapped_type:  # Only add space if type is not empty
                return_type = " " + mapped_type

        # Build method signature with receiver
        receiver = f"obj *{class_name}"
        if params_str:
            func_signature = f"func ({receiver}) {self._to_go_method_name(method.name)}({params_str}){return_type}"
        else:
            func_signature = f"func ({receiver}) {self._to_go_method_name(method.name)}(){return_type}"

        # Convert method body
        self.current_function = method.name
        body = self._convert_method_statements(method.body, class_name)
        self.current_function = None

        return func_signature + " {\n" + body + "\n}"

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
            return f"    {expr}"
        else:
            return self._convert_statement(stmt)

    def _convert_method_assignment(self, stmt: ast.Assign, class_name: str) -> str:
        """Convert method assignment with proper obj handling."""
        value_expr = self._convert_method_expression(stmt.value, class_name)
        statements = []

        for target in stmt.targets:
            if isinstance(target, ast.Name):
                # Local variable assignment
                self._infer_type_from_value(stmt.value)
                statements.append(f"    {target.id} := {value_expr}")
            elif isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    # Instance variable assignment: self.attr = value -> obj.Attr = value
                    field_name = self._to_camel_case(target.attr)
                    statements.append(f"    obj.{field_name} = {value_expr}")
                else:
                    # Regular attribute assignment
                    obj_expr = self._convert_method_expression(target.value, class_name)
                    statements.append(f"    {obj_expr}.{self._to_camel_case(target.attr)} = {value_expr}")

        return "\n".join(statements)

    def _convert_method_annotated_assignment(self, stmt: ast.AnnAssign, class_name: str) -> str:
        """Convert method annotated assignment with proper obj handling."""
        if stmt.value:
            value_expr = self._convert_method_expression(stmt.value, class_name)
        else:
            # Default value based on type
            type_name = self._map_type_annotation(stmt.annotation)
            value_expr = self._get_default_value(type_name)

        if isinstance(stmt.target, ast.Name):
            # Local variable with type annotation
            var_type = self._map_type_annotation(stmt.annotation)
            return f"    var {stmt.target.id} {var_type} = {value_expr}"
        elif isinstance(stmt.target, ast.Attribute):
            if isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                # Instance variable: self.attr: type = value -> obj.Attr = value
                field_name = self._to_camel_case(stmt.target.attr)
                return f"    obj.{field_name} = {value_expr}"

        return "    // TODO: Complex annotated assignment"

    def _convert_method_aug_assignment(self, stmt: ast.AugAssign, class_name: str) -> str:
        """Convert method augmented assignment with proper obj handling."""
        value_expr = self._convert_method_expression(stmt.value, class_name)

        # Map augmented assignment operators
        op_map = {
            ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=", ast.Div: "/=",
            ast.FloorDiv: "/=", ast.Mod: "%=", ast.BitOr: "|=",
            ast.BitXor: "^=", ast.BitAnd: "&=", ast.LShift: "<<=", ast.RShift: ">>="
        }

        op = op_map.get(type(stmt.op), "/*UNKNOWN_OP*/")

        if isinstance(stmt.target, ast.Name):
            return f"    {stmt.target.id} {op} {value_expr}"
        elif isinstance(stmt.target, ast.Attribute):
            if isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                field_name = self._to_camel_case(stmt.target.attr)
                return f"    obj.{field_name} {op} {value_expr}"

        return "    // TODO: Complex augmented assignment"

    def _convert_method_return(self, stmt: ast.Return, class_name: str) -> str:
        """Convert method return statement."""
        if stmt.value:
            value_expr = self._convert_method_expression(stmt.value, class_name)
            return f"    return {value_expr}"
        return "    return"

    def _convert_method_if(self, stmt: ast.If, class_name: str) -> str:
        """Convert if statement in method context."""
        condition = self._convert_method_expression(stmt.test, class_name)
        then_body = self._convert_method_statements(stmt.body, class_name)
        if_part = f"    if {condition} {{\n{then_body}\n    }}"

        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif chain
                else_body = self._convert_method_if(stmt.orelse[0], class_name).strip()
                return f"{if_part} else {else_body}"
            else:
                # regular else
                else_body = self._convert_method_statements(stmt.orelse, class_name)
                return if_part + " else {\n" + else_body + "\n    }"
        else:
            return if_part

    def _convert_method_expression(self, expr: ast.expr, class_name: str) -> str:
        """Convert method expression with class context."""
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                # self.attr -> obj.Attr
                return f"obj.{self._to_camel_case(expr.attr)}"
            else:
                # obj.attr or obj.method()
                obj_expr = self._convert_method_expression(expr.value, class_name)
                return f"{obj_expr}.{self._to_camel_case(expr.attr)}"
        elif isinstance(expr, ast.Call):
            return self._convert_method_call(expr, class_name)
        elif isinstance(expr, ast.BinOp):
            # Handle binary operations with proper obj conversion
            left = self._convert_method_expression(expr.left, class_name)
            right = self._convert_method_expression(expr.right, class_name)

            op_map = {
                ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
                ast.FloorDiv: "/", ast.Mod: "%",
                ast.LShift: "<<", ast.RShift: ">>",
                ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&"
            }

            if isinstance(expr.op, ast.Pow):
                return f"math.Pow({left}, {right})"

            op = op_map.get(type(expr.op), "/*UNKNOWN_OP*/")
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
                # self.method() -> obj.Method()
                method_name = self._to_go_method_name(expr.func.attr)
                args = [self._convert_method_expression(arg, class_name) for arg in expr.args]
                args_str = ", ".join(args)
                return f"obj.{method_name}({args_str})"
            else:
                # Handle string methods and other attribute calls
                obj_expr = self._convert_method_expression(expr.func.value, class_name)
                method_name = expr.func.attr
                args = [self._convert_method_expression(arg, class_name) for arg in expr.args]

                # Handle string methods
                if method_name in ["upper", "lower", "strip", "find", "replace", "split"]:
                    if method_name == "upper":
                        return f"mgen.StrOps.Upper({obj_expr})"
                    elif method_name == "lower":
                        return f"mgen.StrOps.Lower({obj_expr})"
                    elif method_name == "strip":
                        if args:
                            return f"mgen.StrOps.StripChars({obj_expr}, {args[0]})"
                        else:
                            return f"mgen.StrOps.Strip({obj_expr})"
                    elif method_name == "find":
                        return f"mgen.StrOps.Find({obj_expr}, {args[0]})"
                    elif method_name == "replace":
                        return f"mgen.StrOps.Replace({obj_expr}, {args[0]}, {args[1]})"
                    elif method_name == "split":
                        if args:
                            return f"mgen.StrOps.SplitSep({obj_expr}, {args[0]})"
                        else:
                            return f"mgen.StrOps.Split({obj_expr})"

                # Regular method call
                args_str = ", ".join(args)
                return f"{obj_expr}.{self._to_go_method_name(method_name)}({args_str})"
        else:
            # Handle regular function calls like len() with method context
            if isinstance(expr.func, ast.Name):
                func_name = expr.func.id
                args = [self._convert_method_expression(arg, class_name) for arg in expr.args]

                # Handle built-in functions with method context
                if func_name == "len":
                    return f"mgen.Builtins.Len({args[0]})"
                elif func_name == "abs":
                    return f"mgen.Builtins.Abs({args[0]})"
                elif func_name == "min":
                    return f"mgen.Builtins.Min({args[0]})"
                elif func_name == "max":
                    return f"mgen.Builtins.Max({args[0]})"
                elif func_name == "sum":
                    return f"mgen.Builtins.Sum({args[0]})"
                elif func_name == "bool":
                    return f"mgen.ToBool({args[0]})"
                elif func_name == "int":
                    return f"mgen.ToInt({args[0]})"
                elif func_name == "float":
                    return f"mgen.ToFloat({args[0]})"
                elif func_name == "str":
                    return f"mgen.ToStr({args[0]})"
                elif func_name == "range":
                    range_args = ", ".join(args)
                    return f"mgen.NewRange({range_args})"
                else:
                    # Check if this is a class constructor
                    if func_name in self.struct_info:
                        args_str = ", ".join(args)
                        return f"New{func_name}({args_str})"
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
            op_map = {
                ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
                ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!="
            }
            op_str = op_map.get(type(op), "/*UNKNOWN_OP*/")
            comp_expr = self._convert_method_expression(comp, class_name)
            result = f"({result} {op_str} {comp_expr})"

        return result

    def _convert_function(self, node: ast.FunctionDef) -> str:
        """Convert Python function to Go function."""
        # Build parameter list
        params = []
        for arg in node.args.args:
            param_type = self._infer_parameter_type(arg, node)
            params.append(f"{arg.arg} {param_type}")

        params_str = ", ".join(params)

        # Get return type
        return_type = ""
        if node.returns:
            mapped_type = self._map_type_annotation(node.returns)
            if mapped_type:  # Only add space if type is not empty
                return_type = " " + mapped_type
        else:
            # Infer return type from function body if no annotation
            inferred_type = self._infer_return_type(node)
            if inferred_type:
                return_type = " " + inferred_type

        # Build function signature
        func_signature = f"func {node.name}({params_str}){return_type}"

        # Convert function body
        self.current_function = node.name
        self.declared_vars = set()  # Reset for new function
        # Add parameters to declared variables
        for arg in node.args.args:
            self.declared_vars.add(arg.arg)
        body = self._convert_statements(node.body)
        self.current_function = None

        return func_signature + " {\n" + body + "\n}"

    def _convert_statements(self, statements: list[ast.stmt]) -> str:
        """Convert a list of statements."""
        converted = []
        for stmt in statements:
            converted.append(self._convert_statement(stmt))
        return "\n".join(converted)

    def _convert_statement(self, stmt: ast.stmt) -> str:
        """Convert a Python statement to Go."""
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
            return f"    // TODO: Implement {type(stmt).__name__}"

    def _convert_return(self, stmt: ast.Return) -> str:
        """Convert return statement."""
        if stmt.value:
            value_expr = self._convert_expression(stmt.value)
            return f"    return {value_expr}"
        return "    return"

    def _convert_assignment(self, stmt: ast.Assign) -> str:
        """Convert assignment statement."""
        value_expr = self._convert_expression(stmt.value)
        statements = []

        for target in stmt.targets:
            if isinstance(target, ast.Name):
                if target.id in self.declared_vars:
                    # Variable already declared, use assignment
                    statements.append(f"    {target.id} = {value_expr}")
                else:
                    # First declaration of variable
                    self.declared_vars.add(target.id)
                    var_type = self._infer_type_from_value(stmt.value)
                    # Use := for constructor calls and interface{} for cleaner code
                    if var_type == "interface{}" or self._is_constructor_call(stmt.value):
                        statements.append(f"    {target.id} := {value_expr}")
                    else:
                        statements.append(f"    var {target.id} {var_type} = {value_expr}")

        return "\n".join(statements)

    def _convert_annotated_assignment(self, stmt: ast.AnnAssign) -> str:
        """Convert annotated assignment."""
        var_type = self._map_type_annotation(stmt.annotation)

        if stmt.value:
            value_expr = self._convert_expression(stmt.value)
            target_id = stmt.target.id if isinstance(stmt.target, ast.Name) else str(stmt.target)
            return f"    var {target_id} {var_type} = {value_expr}"
        else:
            default_value = self._get_default_value(var_type)
            target_id = stmt.target.id if isinstance(stmt.target, ast.Name) else str(stmt.target)
            return f"    var {target_id} {var_type} = {default_value}"

    def _convert_aug_assignment(self, stmt: ast.AugAssign) -> str:
        """Convert augmented assignment."""
        value_expr = self._convert_expression(stmt.value)

        op_map = {
            ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=", ast.Div: "/=",
            ast.FloorDiv: "/=", ast.Mod: "%=", ast.BitOr: "|=",
            ast.BitXor: "^=", ast.BitAnd: "&=", ast.LShift: "<<=", ast.RShift: ">>="
        }

        op = op_map.get(type(stmt.op), "/*UNKNOWN_OP*/")

        if isinstance(stmt.target, ast.Name):
            return f"    {stmt.target.id} {op} {value_expr}"

        return "    // TODO: Complex augmented assignment"

    def _convert_if(self, stmt: ast.If) -> str:
        """Convert if statement."""
        condition = self._convert_expression(stmt.test)
        then_body = self._convert_statements(stmt.body)
        if_part = f"    if {condition} {{\n{then_body}\n    }}"

        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif chain
                else_body = self._convert_if(stmt.orelse[0]).strip()
                return f"{if_part} else {else_body}"
            else:
                # regular else
                else_body = self._convert_statements(stmt.orelse)
                return if_part + " else {\n" + else_body + "\n    }"
        else:
            return if_part

    def _convert_while(self, stmt: ast.While) -> str:
        """Convert while loop."""
        condition = self._convert_expression(stmt.test)
        body = self._convert_statements(stmt.body)
        return "    for " + condition + " {\n" + body + "\n    }"

    def _convert_for(self, stmt: ast.For) -> str:
        """Convert for loop."""
        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name) and stmt.iter.func.id == "range":
            # Range-based for loop
            range_args = [self._convert_expression(arg) for arg in stmt.iter.args]
            target_name = stmt.target.id if isinstance(stmt.target, ast.Name) else "i"

            if len(range_args) == 1:
                # range(n)
                stop = range_args[0]
                body = self._convert_statements(stmt.body)
                return f"    for {target_name} := 0; {target_name} < {stop}; {target_name}++ {{\n{body}\n    }}"
            elif len(range_args) == 2:
                # range(start, stop)
                start, stop = range_args
                body = self._convert_statements(stmt.body)
                return f"    for {target_name} := {start}; {target_name} < {stop}; {target_name}++ {{\n{body}\n    }}"
            elif len(range_args) == 3:
                # range(start, stop, step)
                start, stop, step = range_args
                body = self._convert_statements(stmt.body)
                return f"    for {target_name} := {start}; {target_name} < {stop}; {target_name} += {step} {{\n{body}\n    }}"
            else:
                # Invalid range arguments
                body = self._convert_statements(stmt.body)
                return f"    for {target_name} := 0; {target_name} < 0; {target_name}++ {{\n{body}\n    }}"  # Empty loop
        else:
            # Iteration over container
            container_expr = self._convert_expression(stmt.iter)
            target_name = stmt.target.id if isinstance(stmt.target, ast.Name) else "item"
            body = self._convert_statements(stmt.body)
            return f"    for _, {target_name} := range {container_expr} {{\n{body}\n    }}"

    def _convert_expression_statement(self, stmt: ast.Expr) -> str:
        """Convert expression statement."""
        expr = self._convert_expression(stmt.value)
        return f"    {expr}"

    def _convert_expression(self, expr: ast.expr) -> str:
        """Convert Python expression to Go."""
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
        elif isinstance(expr, ast.List):
            return self._convert_list_literal(expr)
        elif isinstance(expr, ast.Dict):
            return self._convert_dict_literal(expr)
        elif isinstance(expr, ast.Set):
            return self._convert_set_literal(expr)
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
        if isinstance(expr.value, str):
            return f'"{expr.value}"'
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        elif expr.value is None:
            return "nil"
        elif isinstance(expr.value, float):
            # Convert whole floats to ints for cleaner code (1.0 -> 1)
            if expr.value.is_integer():
                return str(int(expr.value))
            return str(expr.value)
        else:
            return str(expr.value)

    def _convert_binop(self, expr: ast.BinOp) -> str:
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
            return f"math.Pow({left}, {right})"

        op = op_map.get(type(expr.op), "/*UNKNOWN_OP*/")
        return f"({left} {op} {right})"

    def _convert_unaryop(self, expr: ast.UnaryOp) -> str:
        """Convert unary operations."""
        operand = self._convert_expression(expr.operand)

        op_map = {
            ast.UAdd: "+", ast.USub: "-", ast.Not: "!", ast.Invert: "^"
        }

        op = op_map.get(type(expr.op), "/*UNKNOWN_OP*/")
        return f"({op}{operand})"

    def _convert_compare(self, expr: ast.Compare) -> str:
        """Convert comparison operations."""
        left = self._convert_expression(expr.left)
        result = left

        for op, comp in zip(expr.ops, expr.comparators):
            op_map = {
                ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
                ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!="
            }
            op_str = op_map.get(type(op), "/*UNKNOWN_OP*/")
            comp_expr = self._convert_expression(comp)
            result = f"({result} {op_str} {comp_expr})"

        return result

    def _convert_call(self, expr: ast.Call) -> str:
        """Convert function calls."""
        if isinstance(expr.func, ast.Name):
            func_name = expr.func.id
            args = [self._convert_expression(arg) for arg in expr.args]

            # Handle built-in functions
            if func_name == "print":
                args_str = ", ".join(args)
                return f"mgen.Print({args_str})"
            elif func_name == "len":
                return f"mgen.Builtins.Len({args[0]})"
            elif func_name == "abs":
                return f"mgen.Builtins.Abs({args[0]})"
            elif func_name == "min":
                return f"mgen.Builtins.Min({args[0]})"
            elif func_name == "max":
                return f"mgen.Builtins.Max({args[0]})"
            elif func_name == "sum":
                return f"mgen.Builtins.Sum({args[0]})"
            elif func_name == "bool":
                return f"mgen.Builtins.BoolValue({args[0]})"
            elif func_name == "str":
                return f"mgen.ToStr({args[0]})"
            elif func_name == "range":
                range_args = ", ".join(args)
                return f"mgen.NewRange({range_args})"
            else:
                # Check if this is a class constructor
                if func_name in self.struct_info:
                    args_str = ", ".join(args)
                    return f"New{func_name}({args_str})"
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
                    return f"mgen.StrOps.Upper({obj_expr})"
                elif method_name == "lower":
                    return f"mgen.StrOps.Lower({obj_expr})"
                elif method_name == "strip":
                    if args:
                        return f"mgen.StrOps.StripChars({obj_expr}, {args[0]})"
                    else:
                        return f"mgen.StrOps.Strip({obj_expr})"
                elif method_name == "find":
                    return f"mgen.StrOps.Find({obj_expr}, {args[0]})"
                elif method_name == "replace":
                    return f"mgen.StrOps.Replace({obj_expr}, {args[0]}, {args[1]})"
                elif method_name == "split":
                    if args:
                        return f"mgen.StrOps.SplitSep({obj_expr}, {args[0]})"
                    else:
                        return f"mgen.StrOps.Split({obj_expr})"

            # Regular method call
            args_str = ", ".join(args)
            return f"{obj_expr}.{self._to_go_method_name(method_name)}({args_str})"

        return "/* Complex method call */"

    def _convert_attribute(self, expr: ast.Attribute) -> str:
        """Convert attribute access."""
        obj_expr = self._convert_expression(expr.value)
        return f"{obj_expr}.{self._to_camel_case(expr.attr)}"

    def _convert_list_literal(self, expr: ast.List) -> str:
        """Convert list literal to Go slice literal."""
        if not expr.elts:
            # Empty list
            return "[]interface{}{}"

        # Try to infer a common type for all elements
        element_types = [self._infer_type_from_value(elt) for elt in expr.elts]
        if element_types and all(t == element_types[0] and t != "interface{}" for t in element_types):
            # All elements have the same specific type
            element_type = element_types[0]
            elements = [self._convert_expression(elt) for elt in expr.elts]
            elements_str = ", ".join(elements)
            return f"[]{element_type}{{{{{elements_str}}}}}"
        else:
            # Mixed types or interface{}, use interface{}
            elements = [self._convert_expression(elt) for elt in expr.elts]
            elements_str = ", ".join(elements)
            return f"[]interface{{{{{elements_str}}}}}"

    def _convert_dict_literal(self, expr: ast.Dict) -> str:
        """Convert dict literal to Go map literal."""
        if not expr.keys:
            # Empty dict
            return "make(map[interface{}]interface{})"

        # Check for None keys (dictionary unpacking with **)
        has_unpacking = any(key is None for key in expr.keys)

        if has_unpacking:
            # Dictionary unpacking present, use interface{} for safety
            pairs = []
            for key, value in zip(expr.keys, expr.values):
                if key is not None:
                    key_str = self._convert_expression(key)
                    value_str = self._convert_expression(value)
                    pairs.append(f"{key_str}: {value_str}")
                # Note: actual unpacking (**dict) would need runtime handling
            pairs_str = ", ".join(pairs)
            return f"map[interface{{}}]interface{{}}{{{{{pairs_str}}}}}"

        # Try to infer common types for keys and values (all keys are non-None)
        key_types = [self._infer_type_from_value(key) for key in expr.keys if key is not None]
        value_types = [self._infer_type_from_value(value) for value in expr.values]

        if (key_types and all(t == key_types[0] and t != "interface{}" for t in key_types) and
            value_types and all(t == value_types[0] and t != "interface{}" for t in value_types)):
            # All keys and values have specific types
            key_type = key_types[0]
            value_type = value_types[0]
            pairs = []
            for key, value in zip(expr.keys, expr.values):
                if key is not None:
                    key_str = self._convert_expression(key)
                    value_str = self._convert_expression(value)
                    pairs.append(f"{key_str}: {value_str}")
            pairs_str = ", ".join(pairs)
            return f"map[{key_type}]{value_type}{{{{{pairs_str}}}}}"
        else:
            # Mixed types or interface{}, use interface{}
            pairs = []
            for key, value in zip(expr.keys, expr.values):
                if key is not None:
                    key_str = self._convert_expression(key)
                    value_str = self._convert_expression(value)
                    pairs.append(f"{key_str}: {value_str}")
            pairs_str = ", ".join(pairs)
            return f"map[interface{{}}]interface{{}}{{{{{pairs_str}}}}}"

    def _convert_set_literal(self, expr: ast.Set) -> str:
        """Convert set literal to Go map literal (sets as map[T]bool)."""
        if not expr.elts:
            # Empty set
            return "make(map[interface{}]bool)"
        elements = []
        for elt in expr.elts:
            elt_str = self._convert_expression(elt)
            elements.append(f"{elt_str}: true")
        elements_str = ", ".join(elements)
        return f"map[interface{{}}]bool{{{{{elements_str}}}}}"

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
            range_call = f"mgen.NewRange({', '.join(range_args)})"

            # Create transform function
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)
            transform_lambda = f"func(item interface{{}}) interface{{}} {{ {target_name} := item.(int); return {transform_expr} }}"

            if conditions:
                # With condition
                condition_expr = self._convert_expression(conditions[0])
                condition_lambda = f"func(item interface{{}}) bool {{ {target_name} := item.(int); return {condition_expr} }}"
                return f"mgen.Comprehensions.ListComprehensionWithFilter({range_call}, {transform_lambda}, {condition_lambda})"
            else:
                # No condition
                return f"mgen.Comprehensions.ListComprehension({range_call}, {transform_lambda})"
        else:
            # Container iteration
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)
            transform_lambda = f"func(item interface{{}}) interface{{}} {{ {target_name} := item; return {transform_expr} }}"

            if conditions:
                condition_expr = self._convert_expression(conditions[0])
                condition_lambda = f"func(item interface{{}}) bool {{ {target_name} := item; return {condition_expr} }}"
                return f"mgen.Comprehensions.ListComprehensionWithFilter({container_expr}, {transform_lambda}, {condition_lambda})"
            else:
                return f"mgen.Comprehensions.ListComprehension({container_expr}, {transform_lambda})"

    def _convert_dict_comprehension(self, expr: ast.DictComp) -> str:
        """Convert dictionary comprehensions."""
        # Extract comprehension components
        key_expr = expr.key
        value_expr = expr.value
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]
            range_call = f"mgen.NewRange({', '.join(range_args)})"
            target_name = target.id if isinstance(target, ast.Name) else "x"

            key_transform = self._convert_expression(key_expr)
            value_transform = self._convert_expression(value_expr)
            transform_lambda = f"func(item interface{{}}) (interface{{}}, interface{{}}) {{ {target_name} := item.(int); return {key_transform}, {value_transform} }}"

            return f"mgen.Comprehensions.DictComprehension({range_call}, {transform_lambda})"
        else:
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            key_transform = self._convert_expression(key_expr)
            value_transform = self._convert_expression(value_expr)
            transform_lambda = f"func(item interface{{}}) (interface{{}}, interface{{}}) {{ {target_name} := item; return {key_transform}, {value_transform} }}"

            return f"mgen.Comprehensions.DictComprehension({container_expr}, {transform_lambda})"

    def _convert_set_comprehension(self, expr: ast.SetComp) -> str:
        """Convert set comprehensions."""
        # Extract comprehension components
        element_expr = expr.elt
        target = expr.generators[0].target
        iter_expr = expr.generators[0].iter

        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            range_args = [self._convert_expression(arg) for arg in iter_expr.args]
            range_call = f"mgen.NewRange({', '.join(range_args)})"
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)
            transform_lambda = f"func(item interface{{}}) interface{{}} {{ {target_name} := item.(int); return {transform_expr} }}"

            return f"mgen.Comprehensions.SetComprehension({range_call}, {transform_lambda})"
        else:
            container_expr = self._convert_expression(iter_expr)
            target_name = target.id if isinstance(target, ast.Name) else "x"
            transform_expr = self._convert_expression(element_expr)
            transform_lambda = f"func(item interface{{}}) interface{{}} {{ {target_name} := item; return {transform_expr} }}"

            return f"mgen.Comprehensions.SetComprehension({container_expr}, {transform_lambda})"

    # Helper methods for type inference and mapping

    def _map_type_annotation(self, annotation: ast.expr) -> str:
        """Map Python type annotation to Go type."""
        if isinstance(annotation, ast.Name):
            return self.type_map.get(annotation.id, "interface{}")
        elif isinstance(annotation, ast.Subscript):
            # Handle subscripted types like list[int], dict[str, int], etc.
            if isinstance(annotation.value, ast.Name):
                container_type = annotation.value.id
                if container_type == "list":
                    # list[int] -> []int
                    if isinstance(annotation.slice, ast.Name):
                        element_type = self.type_map.get(annotation.slice.id, annotation.slice.id)
                        return f"[]{element_type}"
                    return "[]interface{}"
                elif container_type == "dict":
                    # dict[str, int] -> map[string]int
                    if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) == 2:
                        key_type = self._map_type_annotation(annotation.slice.elts[0])
                        value_type = self._map_type_annotation(annotation.slice.elts[1])
                        return f"map[{key_type}]{value_type}"
                    return "map[interface{}]interface{}"
                elif container_type == "set":
                    # set[int] -> map[int]bool
                    if isinstance(annotation.slice, ast.Name):
                        element_type = self.type_map.get(annotation.slice.id, annotation.slice.id)
                        return f"map[{element_type}]bool"
                    return "map[interface{}]bool"
            return "interface{}"
        elif isinstance(annotation, ast.Constant):
            if annotation.value is None:
                return ""  # None type should be empty return type
            return str(annotation.value)
        else:
            return "interface{}"

    def _infer_type_from_value(self, value: ast.expr) -> str:
        """Infer Go type from Python value."""
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):  # Check bool first since bool is subclass of int
                return "bool"
            elif isinstance(value.value, int):
                return "int"
            elif isinstance(value.value, float):
                return "float64"
            elif isinstance(value.value, str):
                return "string"
        elif isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if value.func.id in self.struct_info:
                return value.func.id
            # Handle built-in function calls
            elif value.func.id == "sum":
                # sum() returns int by default
                return "int"
        elif isinstance(value, ast.ListComp):
            # Infer type from list comprehension element
            element_type = self._infer_comprehension_element_type(value.elt)
            return f"[]{element_type}"
        elif isinstance(value, ast.DictComp):
            # Infer type from dict comprehension key and value
            key_type = self._infer_comprehension_element_type(value.key)
            value_type = self._infer_comprehension_element_type(value.value)
            return f"map[{key_type}]{value_type}"
        elif isinstance(value, ast.SetComp):
            # Infer type from set comprehension element
            element_type = self._infer_comprehension_element_type(value.elt)
            return f"map[{element_type}]bool"

        return "interface{}"

    def _infer_comprehension_element_type(self, expr: ast.expr) -> str:
        """Infer the type of elements produced by a comprehension expression."""
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool"
            elif isinstance(expr.value, int):
                return "int"
            elif isinstance(expr.value, float):
                return "float64"
            elif isinstance(expr.value, str):
                return "string"
        elif isinstance(expr, ast.Name):
            # If it's a simple variable reference, we need more context
            # Default to int for range-based comprehensions
            return "int"
        elif isinstance(expr, ast.BinOp):
            # For binary operations, try to infer from operands
            left_type = self._infer_comprehension_element_type(expr.left)
            right_type = self._infer_comprehension_element_type(expr.right)
            # If both are the same type, use that
            if left_type == right_type:
                return left_type
            # If one is float and one is int, result is float
            if {left_type, right_type} == {"int", "float64"}:
                return "float64"
            return "int"  # Default to int for arithmetic
        elif isinstance(expr, ast.Call):
            # Handle function calls in comprehensions
            if isinstance(expr.func, ast.Attribute):
                # Method calls like str.upper() return string
                attr_name = expr.func.attr
                if attr_name in ("upper", "lower", "strip", "replace"):
                    return "string"
            return "int"  # Default

        return "int"  # Default to int

    def _infer_type_from_assignment(self, stmt: ast.Assign) -> str:
        """Infer type from assignment statement."""
        return self._infer_type_from_value(stmt.value)

    def _infer_parameter_type(self, arg: ast.arg, func: ast.FunctionDef) -> str:
        """Infer parameter type from annotation or context."""
        if arg.annotation:
            return self._map_type_annotation(arg.annotation)
        return "interface{}"

    def _infer_return_type(self, func: ast.FunctionDef) -> str:
        """Infer return type from function body."""
        for stmt in func.body:
            if isinstance(stmt, ast.Return) and stmt.value:
                # Found return statement, infer type
                return "interface{}"  # Default to interface{} for complex expressions
        return ""  # No return statement found

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

    def _get_default_value(self, go_type: str) -> str:
        """Get default value for Go type."""
        defaults = {
            "int": "0",
            "float64": "0.0",
            "bool": "false",
            "string": '""',
            "[]interface{}": "[]interface{}{}",
            "map[interface{}]interface{}": "make(map[interface{}]interface{})",
            "map[interface{}]bool": "make(map[interface{}]bool)",
        }
        # Handle specific slice types like []int, []string, etc.
        if go_type.startswith("[]") and go_type != "[]interface{}":
            return f"{go_type}{{}}"
        # Handle specific map types
        if go_type.startswith("map["):
            return f"make({go_type})"
        return defaults.get(go_type, "nil")


class GoEmitter(AbstractEmitter):
    """Enhanced Go code emitter implementation with comprehensive Python support."""

    def __init__(self, preferences: Optional[BackendPreferences] = None) -> None:
        """Initialize Go emitter."""
        super().__init__(preferences)
        self.converter = MGenPythonToGoConverter()

    def map_python_type(self, python_type: str) -> str:
        """Map Python type to Go type."""
        return self.converter.type_map.get(python_type, "interface{}")

    def emit_function(self, func_node: ast.FunctionDef, type_context: dict[str, str]) -> str:
        """Generate Go function code using the advanced converter."""
        return self.converter._convert_function(func_node)

    def emit_module(self, source_code: str, analysis_result: Any) -> str:
        """Generate complete Go module using the advanced converter."""
        return self.converter.convert_code(source_code)

    def can_use_simple_emission(self, func_node: ast.FunctionDef, type_context: dict[str, str]) -> bool:
        """Check if function can use simple emission strategy."""
        # Advanced converter handles all cases
        return True

    def emit_class(self, node: ast.ClassDef) -> str:
        """Emit Go struct and methods for Python class."""
        return self.converter._convert_class(node)

    def emit_comprehension(self, node: Union[ast.ListComp, ast.DictComp, ast.SetComp]) -> str:
        """Emit Go code for comprehensions."""
        if isinstance(node, ast.ListComp):
            return self.converter._convert_list_comprehension(node)
        elif isinstance(node, ast.DictComp):
            return self.converter._convert_dict_comprehension(node)
        elif isinstance(node, ast.SetComp):
            return self.converter._convert_set_comprehension(node)
        else:
            return "/* Unsupported comprehension */"
