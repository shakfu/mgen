"""Go code emitter for MGen."""

import ast
from typing import Any, Dict

from ..base import AbstractEmitter


class GoEmitter(AbstractEmitter):
    """Go code emitter implementation."""

    def __init__(self):
        """Initialize Go emitter."""
        self.type_map = {
            "int": "int",
            "float": "float64",
            "bool": "bool",
            "str": "string",
            "void": "",
        }

    def map_python_type(self, python_type: str) -> str:
        """Map Python type to Go type."""
        return self.type_map.get(python_type, "int")

    def emit_function(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> str:
        """Generate Go function code."""
        # Get function name
        func_name = func_node.name

        # Build parameter list
        params = []
        for arg in func_node.args.args:
            param_type = self.map_python_type(type_context.get(arg.arg, "int"))
            params.append(f"{arg.arg} {param_type}")

        # Get return type
        return_type = self.map_python_type(type_context.get("__return__", "void"))

        # Build function signature
        params_str = ", ".join(params)

        if return_type and return_type != "":
            signature = f"func {func_name}({params_str}) {return_type}"
        else:
            signature = f"func {func_name}({params_str})"

        # Generate function body (simplified)
        body = self._emit_function_body(func_node, type_context)

        return f"{signature} {{\n{body}\n}}"

    def emit_module(self, source_code: str, analysis_result: Any) -> str:
        """Generate complete Go module."""
        # Parse AST
        tree = ast.parse(source_code)

        # Start with package declaration
        parts = ["package main", "", 'import "fmt"', ""]

        # Generate functions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Simple type context for demonstration
                type_context = self._infer_simple_types(node)
                func_code = self.emit_function(node, type_context)
                functions.append(func_code)

        # Add main function if not present
        if not any("main" in func for func in functions):
            main_func = """func main() {
    fmt.Println("Hello from MGen-generated Go code!")
}"""
            functions.append(main_func)

        # Combine all parts
        parts.extend(functions)
        return "\n\n".join(parts)

    def can_use_simple_emission(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> bool:
        """Check if function can use simple emission strategy."""
        # For now, assume all functions can use simple emission
        return True

    def _emit_function_body(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> str:
        """Generate function body (simplified implementation)."""
        if len(func_node.body) == 1 and isinstance(func_node.body[0], ast.Return):
            # Simple return statement
            return_node = func_node.body[0]
            if isinstance(return_node.value, ast.BinOp):
                # Simple binary operation like x + y
                if isinstance(return_node.value.op, ast.Add):
                    left = self._emit_expression(return_node.value.left)
                    right = self._emit_expression(return_node.value.right)
                    return f"    return {left} + {right}"
                elif isinstance(return_node.value.op, ast.Mult):
                    left = self._emit_expression(return_node.value.left)
                    right = self._emit_expression(return_node.value.right)
                    return f"    return {left} * {right}"
            elif isinstance(return_node.value, ast.Name):
                return f"    return {return_node.value.id}"
            elif isinstance(return_node.value, ast.Constant):
                return f"    return {return_node.value.value}"

        # Default implementation for complex functions
        return "    // TODO: Implement complex function body"

    def _emit_expression(self, expr: ast.expr) -> str:
        """Emit Go expression from Python AST node."""
        if isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.Constant):
            if isinstance(expr.value, str):
                return f'"{expr.value}"'
            return str(expr.value)
        elif isinstance(expr, ast.BinOp):
            left = self._emit_expression(expr.left)
            right = self._emit_expression(expr.right)
            if isinstance(expr.op, ast.Add):
                return f"({left} + {right})"
            elif isinstance(expr.op, ast.Mult):
                return f"({left} * {right})"
            elif isinstance(expr.op, ast.Sub):
                return f"({left} - {right})"
            elif isinstance(expr.op, ast.Div):
                return f"({left} / {right})"
        return "0"  # Fallback

    def _infer_simple_types(self, func_node: ast.FunctionDef) -> Dict[str, str]:
        """Infer simple types from function annotations."""
        type_context = {}

        # Get parameter types from annotations
        for arg in func_node.args.args:
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    type_context[arg.arg] = arg.annotation.id

        # Get return type from annotation
        if func_node.returns and isinstance(func_node.returns, ast.Name):
            type_context["__return__"] = func_node.returns.id

        return type_context