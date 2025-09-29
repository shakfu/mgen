"""Intermediate Representation for Static Python Code.

This module defines the Static Python IR - an intermediate representation
that bridges the gap between Python AST and C code generation, optimized
for the three-layer architecture.
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .ast_analyzer import StaticComplexity


class IRNodeType(Enum):
    """Types of IR nodes."""

    MODULE = "module"
    FUNCTION = "function"
    VARIABLE = "variable"
    EXPRESSION = "expression"
    STATEMENT = "statement"
    TYPE_DECLARATION = "type_declaration"
    CONTROL_FLOW = "control_flow"


class IRDataType(Enum):
    """IR data types with C mapping information."""

    VOID = ("void", "void")
    INT = ("int", "int")
    FLOAT = ("float", "double")  # Python float maps to C double
    BOOL = ("bool", "bool")
    STRING = ("str", "char*")
    POINTER = ("pointer", "*")
    ARRAY = ("array", "[]")
    STRUCT = ("struct", "struct")
    UNION = ("union", "union")
    FUNCTION_PTR = ("function_ptr", "(*)")

    def __init__(self, python_name: str, c_equivalent: str):
        self.python_name = python_name
        self.c_equivalent = c_equivalent


@dataclass
class IRLocation:
    """Source location information for IR nodes."""

    line: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    filename: Optional[str] = None


@dataclass
class IRAnnotation:
    """Annotations for IR nodes providing metadata."""

    optimization_hints: List[str] = field(default_factory=list)
    performance_notes: List[str] = field(default_factory=list)
    conversion_notes: List[str] = field(default_factory=list)
    intelligence_layer_data: Dict[str, Any] = field(default_factory=dict)


class IRNode(ABC):
    """Base class for all IR nodes."""

    def __init__(self, node_type: IRNodeType, location: Optional[IRLocation] = None):
        self.node_type = node_type
        self.location = location
        self.annotations = IRAnnotation()
        self.children: List[IRNode] = []
        self.parent: Optional[IRNode] = None

    def add_child(self, child: "IRNode"):
        """Add a child node."""
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: "IRNode"):
        """Remove a child node."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def get_ancestors(self) -> List["IRNode"]:
        """Get all ancestor nodes."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def find_children_by_type(self, node_type: IRNodeType) -> List["IRNode"]:
        """Find all children of a specific type."""
        return [child for child in self.children if child.node_type == node_type]

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        pass

    @abstractmethod
    def accept(self, visitor: "IRVisitor") -> Any:
        """Accept a visitor for the visitor pattern."""
        pass


@dataclass
class IRType:
    """Type information in the IR."""

    base_type: IRDataType
    is_const: bool = False
    is_pointer: bool = False
    pointer_depth: int = 0
    array_dimensions: List[Optional[int]] = field(default_factory=list)
    struct_name: Optional[str] = None
    union_name: Optional[str] = None
    qualifiers: Set[str] = field(default_factory=set)

    def is_numeric(self) -> bool:
        """Check if type is numeric."""
        return self.base_type in [IRDataType.INT, IRDataType.FLOAT]

    def is_aggregate(self) -> bool:
        """Check if type is an aggregate (struct/union/array)."""
        return self.base_type in [IRDataType.STRUCT, IRDataType.UNION] or bool(self.array_dimensions)

    def to_c_declaration(self, var_name: str = "") -> str:
        """Generate C type declaration."""
        base = self.base_type.c_equivalent

        if self.base_type == IRDataType.STRUCT and self.struct_name:
            base = f"struct {self.struct_name}"
        elif self.base_type == IRDataType.UNION and self.union_name:
            base = f"union {self.union_name}"

        # Add const qualifier
        if self.is_const:
            base = f"const {base}"

        # Add pointer stars
        stars = "*" * self.pointer_depth
        if self.is_pointer and not self.pointer_depth:
            stars = "*"

        # Add array dimensions
        arrays = "".join(f"[{dim if dim else ''}]" for dim in self.array_dimensions)

        return f"{base} {stars}{var_name}{arrays}".strip()


class IRModule(IRNode):
    """IR representation of a Python module."""

    def __init__(self, name: str, location: Optional[IRLocation] = None):
        super().__init__(IRNodeType.MODULE, location)
        self.name = name
        self.imports: List[str] = []
        self.functions: List[IRFunction] = []
        self.global_variables: List[IRVariable] = []
        self.type_declarations: List[IRTypeDeclaration] = []

    def add_function(self, function: "IRFunction"):
        """Add a function to the module."""
        self.add_child(function)
        self.functions.append(function)

    def add_global_variable(self, variable: "IRVariable"):
        """Add a global variable to the module."""
        self.add_child(variable)
        self.global_variables.append(variable)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "module",
            "name": self.name,
            "imports": self.imports,
            "functions": [f.to_dict() for f in self.functions],
            "global_variables": [v.to_dict() for v in self.global_variables],
            "type_declarations": [t.to_dict() for t in self.type_declarations],
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_module(self)


class IRFunction(IRNode):
    """IR representation of a function."""

    def __init__(self, name: str, return_type: IRType, location: Optional[IRLocation] = None):
        super().__init__(IRNodeType.FUNCTION, location)
        self.name = name
        self.return_type = return_type
        self.parameters: List[IRVariable] = []
        self.local_variables: List[IRVariable] = []
        self.body: List[IRStatement] = []
        self.is_static: bool = False
        self.is_inline: bool = False
        self.complexity: StaticComplexity = StaticComplexity.SIMPLE

    def add_parameter(self, param: "IRVariable"):
        """Add a parameter to the function."""
        param.is_parameter = True
        self.add_child(param)
        self.parameters.append(param)

    def add_local_variable(self, var: "IRVariable"):
        """Add a local variable to the function."""
        self.add_child(var)
        self.local_variables.append(var)

    def add_statement(self, stmt: "IRStatement"):
        """Add a statement to the function body."""
        self.add_child(stmt)
        self.body.append(stmt)

    def get_signature(self) -> str:
        """Get C function signature."""
        param_list = ", ".join(param.ir_type.to_c_declaration(param.name) for param in self.parameters)
        if not param_list:
            param_list = "void"

        modifiers = []
        if self.is_static:
            modifiers.append("static")
        if self.is_inline:
            modifiers.append("inline")

        modifier_str = " ".join(modifiers)
        if modifier_str:
            modifier_str += " "

        return f"{modifier_str}{self.return_type.to_c_declaration(self.name)}({param_list})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "return_type": str(self.return_type),
            "parameters": [p.to_dict() for p in self.parameters],
            "local_variables": [v.to_dict() for v in self.local_variables],
            "body": [s.to_dict() for s in self.body],
            "complexity": self.complexity.name,
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_function(self)


class IRVariable(IRNode):
    """IR representation of a variable."""

    def __init__(self, name: str, ir_type: IRType, location: Optional[IRLocation] = None):
        super().__init__(IRNodeType.VARIABLE, location)
        self.name = name
        self.ir_type = ir_type
        self.initial_value: Optional[IRExpression] = None
        self.is_parameter: bool = False
        self.is_global: bool = False
        self.is_static: bool = False
        self.scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "variable",
            "name": self.name,
            "ir_type": str(self.ir_type),
            "is_parameter": self.is_parameter,
            "is_global": self.is_global,
            "scope": self.scope,
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_variable(self)


class IRStatement(IRNode):
    """Base class for IR statements."""

    def __init__(self, location: Optional[IRLocation] = None):
        super().__init__(IRNodeType.STATEMENT, location)


class IRExpression(IRNode):
    """Base class for IR expressions."""

    def __init__(self, result_type: IRType, location: Optional[IRLocation] = None):
        super().__init__(IRNodeType.EXPRESSION, location)
        self.result_type = result_type


class IRAssignment(IRStatement):
    """IR representation of an assignment statement."""

    def __init__(self, target: IRVariable, value: IRExpression, location: Optional[IRLocation] = None):
        super().__init__(location)
        self.target = target
        self.value = value
        self.add_child(target)
        self.add_child(value)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "assignment", "target": self.target.to_dict(), "value": self.value.to_dict()}

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_assignment(self)


class IRBinaryOperation(IRExpression):
    """IR representation of binary operations."""

    def __init__(
        self,
        left: IRExpression,
        operator: str,
        right: IRExpression,
        result_type: IRType,
        location: Optional[IRLocation] = None,
    ):
        super().__init__(result_type, location)
        self.left = left
        self.operator = operator
        self.right = right
        self.add_child(left)
        self.add_child(right)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "binary_operation",
            "left": self.left.to_dict(),
            "operator": self.operator,
            "right": self.right.to_dict(),
            "result_type": str(self.result_type),
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_binary_operation(self)


class IRLiteral(IRExpression):
    """IR representation of literal values."""

    def __init__(self, value: Any, ir_type: IRType, location: Optional[IRLocation] = None):
        super().__init__(ir_type, location)
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "literal", "value": str(self.value), "ir_type": str(self.result_type)}

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_literal(self)


class IRVariableReference(IRExpression):
    """IR representation of variable references."""

    def __init__(self, variable: IRVariable, location: Optional[IRLocation] = None):
        super().__init__(variable.ir_type, location)
        self.variable = variable

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "variable_reference", "variable": self.variable.name, "ir_type": str(self.result_type)}

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_variable_reference(self)


class IRFunctionCall(IRExpression):
    """IR representation of function calls."""

    def __init__(
        self,
        function_name: str,
        arguments: List[IRExpression],
        return_type: IRType,
        location: Optional[IRLocation] = None,
    ):
        super().__init__(return_type, location)
        self.function_name = function_name
        self.arguments = arguments
        for arg in arguments:
            self.add_child(arg)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "function_call",
            "function_name": self.function_name,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "return_type": str(self.result_type),
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_function_call(self)


class IRReturn(IRStatement):
    """IR representation of return statements."""

    def __init__(self, value: Optional[IRExpression] = None, location: Optional[IRLocation] = None):
        super().__init__(location)
        self.value = value
        if value:
            self.add_child(value)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "return", "value": self.value.to_dict() if self.value else None}

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_return(self)


class IRIf(IRStatement):
    """IR representation of if statements."""

    def __init__(
        self,
        condition: IRExpression,
        then_body: List[IRStatement],
        else_body: Optional[List[IRStatement]] = None,
        location: Optional[IRLocation] = None,
    ):
        super().__init__(location)
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body or []

        self.add_child(condition)
        for stmt in self.then_body:
            self.add_child(stmt)
        for stmt in self.else_body:
            self.add_child(stmt)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "if",
            "condition": self.condition.to_dict(),
            "then_body": [s.to_dict() for s in self.then_body],
            "else_body": [s.to_dict() for s in self.else_body],
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_if(self)


class IRWhile(IRStatement):
    """IR representation of while loops."""

    def __init__(self, condition: IRExpression, body: List[IRStatement], location: Optional[IRLocation] = None):
        super().__init__(location)
        self.condition = condition
        self.body = body

        self.add_child(condition)
        for stmt in body:
            self.add_child(stmt)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "while", "condition": self.condition.to_dict(), "body": [s.to_dict() for s in self.body]}

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_while(self)


class IRFor(IRStatement):
    """IR representation of for loops (range-based)."""

    def __init__(
        self,
        variable: IRVariable,
        start: IRExpression,
        end: IRExpression,
        step: Optional[IRExpression],
        body: List[IRStatement],
        location: Optional[IRLocation] = None,
    ):
        super().__init__(location)
        self.variable = variable
        self.start = start
        self.end = end
        self.step = step
        self.body = body

        self.add_child(variable)
        self.add_child(start)
        self.add_child(end)
        if step:
            self.add_child(step)
        for stmt in body:
            self.add_child(stmt)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "for",
            "variable": self.variable.to_dict(),
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "step": self.step.to_dict() if self.step else None,
            "body": [s.to_dict() for s in self.body],
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_for(self)


class IRTypeDeclaration(IRNode):
    """IR representation of type declarations (structs, unions, enums)."""

    def __init__(self, name: str, declaration_type: str, location: Optional[IRLocation] = None):
        super().__init__(IRNodeType.TYPE_DECLARATION, location)
        self.name = name
        self.declaration_type = declaration_type  # "struct", "union", "enum"
        self.fields: List[IRVariable] = []

    def add_field(self, field: IRVariable):
        """Add a field to the type declaration."""
        self.add_child(field)
        self.fields.append(field)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "type_declaration",
            "name": self.name,
            "declaration_type": self.declaration_type,
            "fields": [f.to_dict() for f in self.fields],
        }

    def accept(self, visitor: "IRVisitor") -> Any:
        return visitor.visit_type_declaration(self)


class IRVisitor(ABC):
    """Visitor interface for IR nodes."""

    @abstractmethod
    def visit_module(self, node: IRModule) -> Any:
        pass

    @abstractmethod
    def visit_function(self, node: IRFunction) -> Any:
        pass

    @abstractmethod
    def visit_variable(self, node: IRVariable) -> Any:
        pass

    @abstractmethod
    def visit_assignment(self, node: IRAssignment) -> Any:
        pass

    @abstractmethod
    def visit_binary_operation(self, node: IRBinaryOperation) -> Any:
        pass

    @abstractmethod
    def visit_literal(self, node: IRLiteral) -> Any:
        pass

    @abstractmethod
    def visit_variable_reference(self, node: IRVariableReference) -> Any:
        pass

    @abstractmethod
    def visit_function_call(self, node: IRFunctionCall) -> Any:
        pass

    @abstractmethod
    def visit_return(self, node: IRReturn) -> Any:
        pass

    @abstractmethod
    def visit_if(self, node: IRIf) -> Any:
        pass

    @abstractmethod
    def visit_while(self, node: IRWhile) -> Any:
        pass

    @abstractmethod
    def visit_for(self, node: IRFor) -> Any:
        pass

    @abstractmethod
    def visit_type_declaration(self, node: IRTypeDeclaration) -> Any:
        pass


class IRBuilder:
    """Builder for constructing IR from Python AST."""

    def __init__(self):
        self.current_module: Optional[IRModule] = None
        self.current_function: Optional[IRFunction] = None
        self.symbol_table: Dict[str, IRVariable] = {}

    def build_from_ast(self, tree: ast.AST, module_name: str = "main") -> IRModule:
        """Build IR from Python AST."""
        self.current_module = IRModule(module_name)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                ir_func = self._build_function(node)
                self.current_module.add_function(ir_func)

        return self.current_module

    def _build_function(self, node: ast.FunctionDef) -> IRFunction:
        """Build IR function from AST function definition."""
        # Extract return type
        return_type = self._extract_ir_type(node.returns) if node.returns else IRType(IRDataType.VOID)

        ir_func = IRFunction(node.name, return_type, self._get_location(node))
        self.current_function = ir_func

        # Add parameters
        for arg in node.args.args:
            param_type = self._extract_ir_type(arg.annotation) if arg.annotation else IRType(IRDataType.VOID)
            param = IRVariable(arg.arg, param_type, self._get_location(arg))
            ir_func.add_parameter(param)
            self.symbol_table[arg.arg] = param

        # Process function body
        for stmt in node.body:
            ir_stmt = self._build_statement(stmt)
            if ir_stmt:
                ir_func.add_statement(ir_stmt)

        return ir_func

    def _build_statement(self, node: ast.stmt) -> Optional[IRStatement]:
        """Build IR statement from AST statement."""
        if isinstance(node, ast.AnnAssign):
            return self._build_annotated_assignment(node)
        elif isinstance(node, ast.Assign):
            return self._build_assignment(node)
        elif isinstance(node, ast.Return):
            return self._build_return(node)
        elif isinstance(node, ast.If):
            return self._build_if(node)
        elif isinstance(node, ast.While):
            return self._build_while(node)
        elif isinstance(node, ast.For):
            return self._build_for(node)

        return None

    def _build_annotated_assignment(self, node: ast.AnnAssign) -> IRStatement:
        """Build annotated assignment (variable declaration)."""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            var_type = self._extract_ir_type(node.annotation)

            var = IRVariable(var_name, var_type, self._get_location(node))
            self.symbol_table[var_name] = var

            if self.current_function:
                self.current_function.add_local_variable(var)

            if node.value:
                value_expr = self._build_expression(node.value)
                return IRAssignment(var, value_expr, self._get_location(node))
            else:
                # Create assignment with None value for declaration only
                return IRAssignment(var, None, self._get_location(node))

        # Fallback for complex targets
        return IRAssignment(None, None, self._get_location(node))

    def _build_assignment(self, node: ast.Assign) -> Optional[IRStatement]:
        """Build regular assignment."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            if target_name in self.symbol_table:
                target_var = self.symbol_table[target_name]
                value_expr = self._build_expression(node.value)
                return IRAssignment(target_var, value_expr, self._get_location(node))

        return None

    def _build_expression(self, node: ast.expr) -> IRExpression:
        """Build IR expression from AST expression."""
        if isinstance(node, ast.Constant):
            return self._build_literal(node)
        elif isinstance(node, ast.Name):
            return self._build_variable_reference(node)
        elif isinstance(node, ast.BinOp):
            return self._build_binary_operation(node)
        elif isinstance(node, ast.Call):
            return self._build_function_call(node)

        # Fallback for unknown expressions
        return IRLiteral(None, IRType(IRDataType.VOID), self._get_location(node))

    def _build_literal(self, node: ast.Constant) -> IRLiteral:
        """Build literal from constant."""
        value = node.value
        if isinstance(value, bool):
            ir_type = IRType(IRDataType.BOOL)
        elif isinstance(value, int):
            ir_type = IRType(IRDataType.INT)
        elif isinstance(value, float):
            ir_type = IRType(IRDataType.FLOAT)
        elif isinstance(value, str):
            ir_type = IRType(IRDataType.STRING)
        else:
            ir_type = IRType(IRDataType.VOID)

        return IRLiteral(value, ir_type, self._get_location(node))

    def _build_variable_reference(self, node: ast.Name) -> IRVariableReference:
        """Build variable reference."""
        var = self.symbol_table.get(node.id)
        if not var:
            # Create a placeholder variable
            var = IRVariable(node.id, IRType(IRDataType.VOID))
            self.symbol_table[node.id] = var

        return IRVariableReference(var, self._get_location(node))

    def _build_binary_operation(self, node: ast.BinOp) -> IRBinaryOperation:
        """Build binary operation."""
        left = self._build_expression(node.left)
        right = self._build_expression(node.right)

        # Infer result type (simplified)
        result_type = left.result_type  # Simplified type inference

        operator = self._get_operator_string(node.op)

        return IRBinaryOperation(left, operator, right, result_type, self._get_location(node))

    def _build_function_call(self, node: ast.Call) -> IRFunctionCall:
        """Build function call."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            arguments = [self._build_expression(arg) for arg in node.args]

            # Simple return type inference
            return_type = IRType(IRDataType.VOID)  # Would need better inference

            return IRFunctionCall(func_name, arguments, return_type, self._get_location(node))
        else:
            # Handle complex function calls (attribute access, etc.)
            func_name = "complex_call"  # Placeholder for complex calls
            arguments = [self._build_expression(arg) for arg in node.args]
            return_type = IRType(IRDataType.VOID)
            return IRFunctionCall(func_name, arguments, return_type, self._get_location(node))

    def _build_return(self, node: ast.Return) -> IRReturn:
        """Build return statement."""
        value = self._build_expression(node.value) if node.value else None
        return IRReturn(value, self._get_location(node))

    def _build_if(self, node: ast.If) -> IRIf:
        """Build if statement."""
        condition = self._build_expression(node.test)
        then_body = [self._build_statement(stmt) for stmt in node.body]
        then_body = [stmt for stmt in then_body if stmt]  # Filter None

        else_body = []
        if node.orelse:
            else_body = [self._build_statement(stmt) for stmt in node.orelse]
            else_body = [stmt for stmt in else_body if stmt]  # Filter None

        return IRIf(condition, then_body, else_body, self._get_location(node))

    def _build_while(self, node: ast.While) -> IRWhile:
        """Build while loop."""
        condition = self._build_expression(node.test)
        body = [self._build_statement(stmt) for stmt in node.body]
        body = [stmt for stmt in body if stmt]  # Filter None

        return IRWhile(condition, body, self._get_location(node))

    def _build_for(self, node: ast.For) -> Optional[IRFor]:
        """Build for loop (range-based only)."""
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range":
                # Extract range parameters
                args = node.iter.args
                if len(args) == 1:
                    start = IRLiteral(0, IRType(IRDataType.INT))
                    end = self._build_expression(args[0])
                    step = IRLiteral(1, IRType(IRDataType.INT))
                elif len(args) == 2:
                    start = self._build_expression(args[0])
                    end = self._build_expression(args[1])
                    step = IRLiteral(1, IRType(IRDataType.INT))
                elif len(args) == 3:
                    start = self._build_expression(args[0])
                    end = self._build_expression(args[1])
                    step = self._build_expression(args[2])
                else:
                    return None

                # Create loop variable
                if isinstance(node.target, ast.Name):
                    var_name = node.target.id
                    loop_var = IRVariable(var_name, IRType(IRDataType.INT), self._get_location(node.target))
                    self.symbol_table[var_name] = loop_var

                    body = [self._build_statement(stmt) for stmt in node.body]
                    body = [stmt for stmt in body if stmt]  # Filter None

                    return IRFor(loop_var, start, end, step, body, self._get_location(node))

        return None

    def _extract_ir_type(self, annotation: ast.expr) -> IRType:
        """Extract IR type from AST annotation."""
        if isinstance(annotation, ast.Name):
            type_mapping = {
                "int": IRDataType.INT,
                "float": IRDataType.FLOAT,
                "bool": IRDataType.BOOL,
                "str": IRDataType.STRING,
                "void": IRDataType.VOID,
            }
            base_type = type_mapping.get(annotation.id, IRDataType.VOID)
            return IRType(base_type)
        elif isinstance(annotation, ast.Subscript):
            # Handle generic types like list[int]
            if isinstance(annotation.value, ast.Name) and annotation.value.id == "list":
                element_type = self._extract_ir_type(annotation.slice)
                return IRType(IRDataType.POINTER, pointer_depth=1)  # Simplified

        return IRType(IRDataType.VOID)

    def _get_location(self, node: ast.AST) -> IRLocation:
        """Extract location information from AST node."""
        return IRLocation(
            line=node.lineno,
            column=getattr(node, "col_offset", 0),
            end_line=getattr(node, "end_lineno", None),
            end_column=getattr(node, "end_col_offset", None),
        )

    def _get_operator_string(self, op: ast.operator) -> str:
        """Convert AST operator to string."""
        operator_mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
        }
        return operator_mapping.get(type(op), "?")


def build_ir_from_code(source_code: str, module_name: str = "main") -> IRModule:
    """Convenience function to build IR from Python source code."""
    tree = ast.parse(source_code)
    builder = IRBuilder()
    return builder.build_from_ast(tree, module_name)
