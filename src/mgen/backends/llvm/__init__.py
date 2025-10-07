"""LLVM IR backend for MGen.

This backend converts MGen's Static Python IR to LLVM IR using llvmlite,
enabling compilation to native binaries, WebAssembly, and other LLVM targets.
"""

from .backend import LLVMBackend
from .compiler import LLVMCompiler
from .ir_to_llvm import IRToLLVMConverter

__all__ = ["LLVMBackend", "IRToLLVMConverter", "LLVMCompiler"]
