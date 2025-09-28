"""C++ code emitter."""

import ast
from typing import Any, List, Optional

from ..base import AbstractEmitter
from .factory import CppFactory


class CppEmitter(AbstractEmitter):
    """Emitter for generating C++ code from Python AST."""

    def __init__(self):
        """Initialize the C++ emitter."""
        self.factory = CppFactory()
        self.indent_level = 0
        self.indent_size = 4

    def emit_module(self, source_code: str, analysis_result: Optional[Any] = None) -> str:
        """Emit a complete C++ module from Python source."""
        tree = ast.parse(source_code)

        # Generate includes
        includes = [
            self.factory.create_include("iostream"),
            self.factory.create_include("string"),
            self.factory.create_include("vector"),
            self.factory.create_include("map"),
        ]

        # Generate using statements for convenience
        using_statements = [
            "using namespace std;"
        ]

        # Generate functions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(self.emit_function(node))

        # Combine all parts
        parts = includes + [""] + using_statements + [""] + functions
        return "\n".join(parts)

    def emit_function(self, node: ast.FunctionDef) -> str:
        """Emit a C++ function from a Python function definition."""
        # Get return type
        return_type = self._get_return_type(node)

        # Get parameters
        params = []
        for arg in node.args.args:
            param_type = self._get_param_type(arg)
            param = self.factory.create_parameter(arg.arg, param_type)
            params.append(param)

        # Generate function body
        body = self._emit_statements(node.body)

        return self.factory.create_function(node.name, params, return_type, body)

    def emit_statement(self, node: ast.stmt) -> str:
        """Emit a C++ statement from a Python AST node."""
        if isinstance(node, ast.Return):
            return self.emit_return(node)
        elif isinstance(node, ast.Assign):
            return self.emit_assignment(node)
        elif isinstance(node, ast.AugAssign):
            return self.emit_aug_assignment(node)
        elif isinstance(node, ast.If):
            return self.emit_if(node)
        elif isinstance(node, ast.While):
            return self.emit_while(node)
        elif isinstance(node, ast.For):
            return self.emit_for(node)
        elif isinstance(node, ast.Expr):
            return self.emit_expression_statement(node)
        else:
            return f"// TODO: Implement {type(node).__name__}"

    def emit_expression(self, node: ast.expr) -> str:
        """Emit a C++ expression from a Python AST node."""
        if isinstance(node, ast.Constant):
            return self.emit_constant(node)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.BinOp):
            return self.emit_binary_op(node)
        elif isinstance(node, ast.Call):
            return self.emit_call(node)
        elif isinstance(node, ast.Compare):
            return self.emit_compare(node)
        elif isinstance(node, ast.UnaryOp):
            return self.emit_unary_op(node)
        elif isinstance(node, ast.BoolOp):
            return self.emit_bool_op(node)
        else:
            return f"/* TODO: {type(node).__name__} */"

    def emit_return(self, node: ast.Return) -> str:
        """Emit a C++ return statement."""
        if node.value:
            value = self.emit_expression(node.value)
            return self._indent(self.factory.create_return_statement(value))
        return self._indent("return;")

    def emit_assignment(self, node: ast.Assign) -> str:
        """Emit a C++ assignment."""
        value = self.emit_expression(node.value)
        statements = []

        for target in node.targets:
            if isinstance(target, ast.Name):
                # For now, use auto type deduction
                stmt = self._indent(f"auto {target.id} = {value};")
                statements.append(stmt)

        return "\n".join(statements)

    def emit_aug_assignment(self, node: ast.AugAssign) -> str:
        """Emit a C++ augmented assignment."""
        target = self.emit_expression(node.target)
        value = self.emit_expression(node.value)
        op = self._get_aug_op(node.op)
        return self._indent(f"{target} {op}= {value};")

    def emit_if(self, node: ast.If) -> str:
        """Emit a C++ if statement."""
        condition = self.emit_expression(node.test)
        then_body = self._emit_statements(node.body)
        else_body = self._emit_statements(node.orelse) if node.orelse else None
        return self._indent(self.factory.create_if_statement(condition, then_body, else_body))

    def emit_while(self, node: ast.While) -> str:
        """Emit a C++ while loop."""
        condition = self.emit_expression(node.test)
        body = self._emit_statements(node.body)
        return self._indent(self.factory.create_while_loop(condition, body))

    def emit_for(self, node: ast.For) -> str:
        """Emit a C++ for loop (simplified range-based for now)."""
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            # Handle range() calls
            args = node.iter.args
            if len(args) == 1:
                # range(n) -> for(int i = 0; i < n; i++)
                limit = self.emit_expression(args[0])
                init = f"int {node.target.id} = 0"
                condition = f"{node.target.id} < {limit}"
                update = f"{node.target.id}++"
            elif len(args) == 2:
                # range(start, stop) -> for(int i = start; i < stop; i++)
                start = self.emit_expression(args[0])
                stop = self.emit_expression(args[1])
                init = f"int {node.target.id} = {start}"
                condition = f"{node.target.id} < {stop}"
                update = f"{node.target.id}++"
            else:
                # Fallback
                init = f"int {node.target.id} = 0"
                condition = "true"
                update = f"{node.target.id}++"

            body = self._emit_statements(node.body)
            return self._indent(self.factory.create_for_loop(init, condition, update, body))
        else:
            # Range-based for loop for containers
            body = self._emit_statements(node.body)
            iter_expr = self.emit_expression(node.iter)
            return self._indent(f"for (auto {node.target.id} : {iter_expr}) {{\n{body}\n}}")

    def emit_expression_statement(self, node: ast.Expr) -> str:
        """Emit a C++ expression statement."""
        expr = self.emit_expression(node.value)
        return self._indent(f"{expr};")

    def emit_constant(self, node: ast.Constant) -> str:
        """Emit a C++ constant."""
        value = node.value
        if isinstance(value, str):
            return self.factory.create_literal(value, "string")
        elif isinstance(value, bool):
            return self.factory.create_literal(value, "bool")
        elif isinstance(value, float):
            return self.factory.create_literal(value, "float")
        else:
            return self.factory.create_literal(value, "int")

    def emit_binary_op(self, node: ast.BinOp) -> str:
        """Emit a C++ binary operation."""
        left = self.emit_expression(node.left)
        right = self.emit_expression(node.right)
        op = self._get_binary_op(node.op)
        return self.factory.create_binary_op(left, op, right)

    def emit_call(self, node: ast.Call) -> str:
        """Emit a C++ function call."""
        if isinstance(node.func, ast.Name):
            func_name = self._map_function_name(node.func.id)
            args = [self.emit_expression(arg) for arg in node.args]
            return self.factory.create_function_call(func_name, args)
        else:
            return "/* TODO: Complex function call */"

    def emit_compare(self, node: ast.Compare) -> str:
        """Emit a C++ comparison."""
        left = self.emit_expression(node.left)
        result = left

        for i, (op, comparator) in enumerate(zip(node.ops, node.comparators)):
            right = self.emit_expression(comparator)
            cpp_op = self._get_compare_op(op)
            result = f"({result} {cpp_op} {right})"

        return result

    def emit_unary_op(self, node: ast.UnaryOp) -> str:
        """Emit a C++ unary operation."""
        operand = self.emit_expression(node.operand)
        op = self._get_unary_op(node.op)
        return f"({op}{operand})"

    def emit_bool_op(self, node: ast.BoolOp) -> str:
        """Emit a C++ boolean operation."""
        op = " && " if isinstance(node.op, ast.And) else " || "
        values = [self.emit_expression(value) for value in node.values]
        return f"({op.join(values)})"

    def _emit_statements(self, statements: List[ast.stmt]) -> str:
        """Emit multiple statements with proper indentation."""
        self.indent_level += 1
        result = []
        for stmt in statements:
            result.append(self.emit_statement(stmt))
        self.indent_level -= 1
        return "\n".join(result)

    def _indent(self, text: str) -> str:
        """Add indentation to text."""
        indent = " " * (self.indent_level * self.indent_size)
        return indent + text

    def _get_return_type(self, node: ast.FunctionDef) -> str:
        """Get the return type for a function."""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return self.factory.get_type_mapping().get(node.returns.id, "auto")
            elif isinstance(node.returns, ast.Constant):
                if node.returns.value is None:
                    return "void"
        return "auto"

    def _get_param_type(self, arg: ast.arg) -> str:
        """Get the parameter type."""
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                return self.factory.get_type_mapping().get(arg.annotation.id, "auto")
        return "auto"

    def _get_binary_op(self, op: ast.operator) -> str:
        """Convert Python binary operator to C++."""
        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "/", ast.Mod: "%", ast.Pow: "pow",
            ast.LShift: "<<", ast.RShift: ">>",
            ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&"
        }
        return op_map.get(type(op), "/*UNKNOWN_OP*/")

    def _get_compare_op(self, op: ast.cmpop) -> str:
        """Convert Python comparison operator to C++."""
        op_map = {
            ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",
            ast.In: "/* IN */", ast.NotIn: "/* NOT IN */"
        }
        return op_map.get(type(op), "/*UNKNOWN_CMP*/")

    def _get_unary_op(self, op: ast.unaryop) -> str:
        """Convert Python unary operator to C++."""
        op_map = {
            ast.UAdd: "+", ast.USub: "-", ast.Not: "!", ast.Invert: "~"
        }
        return op_map.get(type(op), "/*UNKNOWN_UNARY*/")

    def _get_aug_op(self, op: ast.operator) -> str:
        """Convert Python augmented assignment operator to C++."""
        return self._get_binary_op(op)

    def _map_function_name(self, python_name: str) -> str:
        """Map Python function names to C++ equivalents."""
        name_map = {
            "print": "cout",
            "len": "size",
            "str": "to_string",
            "int": "static_cast<int>",
            "float": "static_cast<double>",
        }
        return name_map.get(python_name, python_name)

    def map_python_type(self, python_type: str) -> str:
        """Map Python type to C++ type."""
        return self.factory.get_type_mapping().get(python_type, "auto")

    def can_use_simple_emission(self, analysis_result: Any) -> bool:
        """Check if simple emission can be used for this code."""
        # For now, always use full emission
        return False