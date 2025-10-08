"""LLVM IR runtime declarations for C runtime library.

This module generates LLVM IR struct definitions and extern function declarations
that correspond to the C runtime library (vec_int, map_int_int, set_int, etc.).
"""

from llvmlite import ir  # type: ignore[import-untyped]


class LLVMRuntimeDeclarations:
    """Generate LLVM IR declarations for C runtime library."""

    def __init__(self, module: ir.Module) -> None:
        """Initialize runtime declarations.

        Args:
            module: LLVM module to add declarations to
        """
        self.module = module
        self.struct_types: dict[str, ir.Type] = {}
        self.function_decls: dict[str, ir.Function] = {}

    def get_vec_int_type(self) -> ir.Type:
        """Get or create vec_int struct type.

        C struct definition:
            typedef struct {
                long long* data;
                size_t size;
                size_t capacity;
            } vec_int;

        Returns:
            LLVM struct type for vec_int
        """
        if "vec_int" in self.struct_types:
            return self.struct_types["vec_int"]

        # Create named struct type (required for alloca)
        # struct vec_int { i64*, i64, i64 }
        # data: i64* (pointer to array of 64-bit integers)
        # size: i64 (size_t on 64-bit systems)
        # capacity: i64 (size_t on 64-bit systems)
        vec_int_type = self.module.context.get_identified_type("struct.vec_int")

        # Only set body if not already defined (avoid re-definition in shared context)
        if not vec_int_type.is_opaque:
            # Type already has a body, just use it
            self.struct_types["vec_int"] = vec_int_type
            return vec_int_type

        vec_int_type.set_body(
            ir.IntType(64).as_pointer(),  # data
            ir.IntType(64),                # size
            ir.IntType(64),                # capacity
        )

        self.struct_types["vec_int"] = vec_int_type
        return vec_int_type

    def declare_vec_int_functions(self) -> None:
        """Declare vec_int C runtime functions in LLVM IR."""
        vec_int_type = self.get_vec_int_type()
        vec_int_ptr = vec_int_type.as_pointer()
        i64 = ir.IntType(64)
        i64_ptr = i64.as_pointer()
        void = ir.VoidType()

        # void vec_int_init_ptr(vec_int* out) - initialize via pointer
        func_type = ir.FunctionType(void, [vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_int_init_ptr")
        self.function_decls["vec_int_init_ptr"] = func

        # void vec_int_push(vec_int* vec, long long value)
        func_type = ir.FunctionType(void, [vec_int_ptr, i64])
        func = ir.Function(self.module, func_type, name="vec_int_push")
        self.function_decls["vec_int_push"] = func

        # long long vec_int_at(vec_int* vec, size_t index)
        func_type = ir.FunctionType(i64, [vec_int_ptr, i64])
        func = ir.Function(self.module, func_type, name="vec_int_at")
        self.function_decls["vec_int_at"] = func

        # size_t vec_int_size(vec_int* vec)
        func_type = ir.FunctionType(i64, [vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_int_size")
        self.function_decls["vec_int_size"] = func

        # void vec_int_free(vec_int* vec)
        func_type = ir.FunctionType(void, [vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_int_free")
        self.function_decls["vec_int_free"] = func

        # long long* vec_int_data(vec_int* vec)
        func_type = ir.FunctionType(i64_ptr, [vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_int_data")
        self.function_decls["vec_int_data"] = func

        # void vec_int_clear(vec_int* vec)
        func_type = ir.FunctionType(void, [vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_int_clear")
        self.function_decls["vec_int_clear"] = func

        # void vec_int_reserve(vec_int* vec, size_t new_capacity)
        func_type = ir.FunctionType(void, [vec_int_ptr, i64])
        func = ir.Function(self.module, func_type, name="vec_int_reserve")
        self.function_decls["vec_int_reserve"] = func

        # void vec_int_set(vec_int* vec, size_t index, long long value)
        func_type = ir.FunctionType(void, [vec_int_ptr, i64, i64])
        func = ir.Function(self.module, func_type, name="vec_int_set")
        self.function_decls["vec_int_set"] = func

    def get_function(self, name: str) -> ir.Function:
        """Get declared function by name.

        Args:
            name: Function name

        Returns:
            LLVM function declaration

        Raises:
            KeyError: If function not declared
        """
        if name not in self.function_decls:
            raise KeyError(f"Function '{name}' not declared. Call declare_*_functions() first.")
        return self.function_decls[name]

    def get_vec_vec_int_type(self) -> ir.Type:
        """Get or create vec_vec_int struct type.

        C struct definition:
            typedef struct {
                vec_int* data;
                size_t size;
                size_t capacity;
            } vec_vec_int;

        Returns:
            LLVM struct type for vec_vec_int
        """
        if "vec_vec_int" in self.struct_types:
            return self.struct_types["vec_vec_int"]

        # Get vec_int type first
        vec_int_type = self.get_vec_int_type()
        vec_int_ptr = vec_int_type.as_pointer()

        # Create named struct type for vec_vec_int
        vec_vec_int_type = self.module.context.get_identified_type("struct.vec_vec_int")

        if not vec_vec_int_type.is_opaque:
            self.struct_types["vec_vec_int"] = vec_vec_int_type
            return vec_vec_int_type

        vec_vec_int_type.set_body(
            vec_int_ptr,       # data: vec_int* (pointer to array of vec_int)
            ir.IntType(64),    # size
            ir.IntType(64),    # capacity
        )

        self.struct_types["vec_vec_int"] = vec_vec_int_type
        return vec_vec_int_type

    def declare_vec_vec_int_functions(self) -> None:
        """Declare vec_vec_int C runtime functions in LLVM IR."""
        vec_vec_int_type = self.get_vec_vec_int_type()
        vec_vec_int_ptr = vec_vec_int_type.as_pointer()
        vec_int_type = self.get_vec_int_type()
        vec_int_ptr = vec_int_type.as_pointer()
        i64 = ir.IntType(64)
        void = ir.VoidType()

        # void vec_vec_int_init_ptr(vec_vec_int* out)
        func_type = ir.FunctionType(void, [vec_vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_vec_int_init_ptr")
        self.function_decls["vec_vec_int_init_ptr"] = func

        # void vec_vec_int_push(vec_vec_int* vec, vec_int* row)
        # Note: row is passed by pointer (avoids struct-by-value issues)
        func_type = ir.FunctionType(void, [vec_vec_int_ptr, vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_vec_int_push")
        self.function_decls["vec_vec_int_push"] = func

        # vec_int* vec_vec_int_at(vec_vec_int* vec, size_t index)
        func_type = ir.FunctionType(vec_int_ptr, [vec_vec_int_ptr, i64])
        func = ir.Function(self.module, func_type, name="vec_vec_int_at")
        self.function_decls["vec_vec_int_at"] = func

        # size_t vec_vec_int_size(vec_vec_int* vec)
        func_type = ir.FunctionType(i64, [vec_vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_vec_int_size")
        self.function_decls["vec_vec_int_size"] = func

        # void vec_vec_int_free(vec_vec_int* vec)
        func_type = ir.FunctionType(void, [vec_vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_vec_int_free")
        self.function_decls["vec_vec_int_free"] = func

        # void vec_vec_int_clear(vec_vec_int* vec)
        func_type = ir.FunctionType(void, [vec_vec_int_ptr])
        func = ir.Function(self.module, func_type, name="vec_vec_int_clear")
        self.function_decls["vec_vec_int_clear"] = func

    def get_string_array_type(self) -> ir.Type:
        """Get or create mgen_string_array_t struct type.

        C struct definition:
            typedef struct {
                char** strings;
                size_t count;
                size_t capacity;
            } mgen_string_array_t;

        Returns:
            LLVM struct type for mgen_string_array_t
        """
        if "string_array" in self.struct_types:
            return self.struct_types["string_array"]

        # Create named struct type
        string_array_type = self.module.context.get_identified_type("struct.mgen_string_array_t")

        if not string_array_type.is_opaque:
            self.struct_types["string_array"] = string_array_type
            return string_array_type

        i8_ptr = ir.IntType(8).as_pointer()  # char*
        i8_ptr_ptr = i8_ptr.as_pointer()      # char**

        string_array_type.set_body(
            i8_ptr_ptr,        # strings: char**
            ir.IntType(64),    # count: size_t
            ir.IntType(64),    # capacity: size_t
        )

        self.struct_types["string_array"] = string_array_type
        return string_array_type

    def declare_string_functions(self) -> None:
        """Declare string operation C runtime functions in LLVM IR."""
        i8_ptr = ir.IntType(8).as_pointer()  # char*
        i64 = ir.IntType(64)
        void = ir.VoidType()
        string_array_type = self.get_string_array_type()
        string_array_ptr = string_array_type.as_pointer()

        # mgen_string_array_t* mgen_str_split(const char* str, const char* delimiter)
        func_type = ir.FunctionType(string_array_ptr, [i8_ptr, i8_ptr])
        func = ir.Function(self.module, func_type, name="mgen_str_split")
        self.function_decls["mgen_str_split"] = func

        # char* mgen_str_lower(const char* str)
        func_type = ir.FunctionType(i8_ptr, [i8_ptr])
        func = ir.Function(self.module, func_type, name="mgen_str_lower")
        self.function_decls["mgen_str_lower"] = func

        # char* mgen_str_strip(const char* str)
        func_type = ir.FunctionType(i8_ptr, [i8_ptr])
        func = ir.Function(self.module, func_type, name="mgen_str_strip")
        self.function_decls["mgen_str_strip"] = func

        # char* mgen_str_concat(const char* str1, const char* str2)
        func_type = ir.FunctionType(i8_ptr, [i8_ptr, i8_ptr])
        func = ir.Function(self.module, func_type, name="mgen_str_concat")
        self.function_decls["mgen_str_concat"] = func

        # const char* mgen_string_array_get(mgen_string_array_t* arr, size_t index)
        func_type = ir.FunctionType(i8_ptr, [string_array_ptr, i64])
        func = ir.Function(self.module, func_type, name="mgen_string_array_get")
        self.function_decls["mgen_string_array_get"] = func

        # size_t mgen_string_array_size(mgen_string_array_t* arr)
        func_type = ir.FunctionType(i64, [string_array_ptr])
        func = ir.Function(self.module, func_type, name="mgen_string_array_size")
        self.function_decls["mgen_string_array_size"] = func

        # void mgen_string_array_free(mgen_string_array_t* arr)
        func_type = ir.FunctionType(void, [string_array_ptr])
        func = ir.Function(self.module, func_type, name="mgen_string_array_free")
        self.function_decls["mgen_string_array_free"] = func

    def declare_all(self) -> None:
        """Declare all runtime library functions and types."""
        self.declare_vec_int_functions()
        self.declare_vec_vec_int_functions()
        self.declare_string_functions()
