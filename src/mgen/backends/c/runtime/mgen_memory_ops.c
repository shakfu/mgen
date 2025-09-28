/**
 * CGen Runtime Library - Memory Management Utilities Implementation
 */

#include "mgen_memory_ops.h"
#include <stdarg.h>

// Memory tracking globals
static int memory_tracking_enabled = 0;
static mgen_memory_stats_t memory_stats = {0};

// Memory pool structure
struct mgen_memory_pool {
    char* data;
    size_t size;
    size_t capacity;
    size_t used;
};

// Scope allocator structure
typedef struct alloc_entry {
    void* ptr;
    struct alloc_entry* next;
} alloc_entry_t;

struct mgen_scope_allocator {
    alloc_entry_t* head;
    size_t count;
};

// Safe memory allocation functions
void* mgen_malloc(size_t size) {
    if (size == 0) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Attempted to allocate 0 bytes");
        return NULL;
    }

    void* ptr = malloc(size);
    if (!ptr) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_MEMORY, "Failed to allocate %zu bytes", size);
        return NULL;
    }

    if (memory_tracking_enabled) {
        memory_stats.total_allocated += size;
        memory_stats.current_allocated += size;
        memory_stats.allocation_count++;
        if (memory_stats.current_allocated > memory_stats.peak_allocated) {
            memory_stats.peak_allocated = memory_stats.current_allocated;
        }
    }

    return ptr;
}

void* mgen_realloc(void* ptr, size_t new_size) {
    if (new_size == 0) {
        if (ptr) {
            mgen_free((void**)&ptr);
        }
        return NULL;
    }

    void* new_ptr = realloc(ptr, new_size);
    if (!new_ptr) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_MEMORY, "Failed to reallocate to %zu bytes", new_size);
        return NULL;
    }

    // Note: tracking size changes in realloc is complex, simplified here
    if (memory_tracking_enabled && !ptr) {
        memory_stats.total_allocated += new_size;
        memory_stats.current_allocated += new_size;
        memory_stats.allocation_count++;
    }

    return new_ptr;
}

void* mgen_calloc(size_t count, size_t size) {
    if (count == 0 || size == 0) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Attempted to allocate 0 elements or 0 bytes");
        return NULL;
    }

    // Check for overflow
    if (count > SIZE_MAX / size) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Integer overflow in calloc");
        return NULL;
    }

    void* ptr = calloc(count, size);
    if (!ptr) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_MEMORY, "Failed to allocate %zu elements of %zu bytes",
                           count, size);
        return NULL;
    }

    if (memory_tracking_enabled) {
        size_t total_size = count * size;
        memory_stats.total_allocated += total_size;
        memory_stats.current_allocated += total_size;
        memory_stats.allocation_count++;
        if (memory_stats.current_allocated > memory_stats.peak_allocated) {
            memory_stats.peak_allocated = memory_stats.current_allocated;
        }
    }

    return ptr;
}

void mgen_free(void** ptr) {
    if (!ptr || !*ptr) {
        return;
    }

    if (memory_tracking_enabled) {
        // Note: We can't track exact size freed without additional bookkeeping
        memory_stats.free_count++;
    }

    free(*ptr);
    *ptr = NULL;
}

// Safe memory operations
mgen_error_t mgen_memcpy_safe(void* dest, size_t dest_size,
                             const void* src, size_t src_size) {
    if (!dest || !src) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL pointer in memcpy");
        return MGEN_ERROR_VALUE;
    }

    if (src_size > dest_size) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_VALUE,
                           "Source size %zu exceeds destination size %zu",
                           src_size, dest_size);
        return MGEN_ERROR_VALUE;
    }

    memcpy(dest, src, src_size);
    return MGEN_OK;
}

mgen_error_t mgen_memmove_safe(void* dest, size_t dest_size,
                              const void* src, size_t src_size) {
    if (!dest || !src) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL pointer in memmove");
        return MGEN_ERROR_VALUE;
    }

    if (src_size > dest_size) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_VALUE,
                           "Source size %zu exceeds destination size %zu",
                           src_size, dest_size);
        return MGEN_ERROR_VALUE;
    }

    memmove(dest, src, src_size);
    return MGEN_OK;
}

mgen_error_t mgen_memset_safe(void* dest, int value, size_t count, size_t dest_size) {
    if (!dest) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL pointer in memset");
        return MGEN_ERROR_VALUE;
    }

    if (count > dest_size) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_VALUE,
                           "Count %zu exceeds destination size %zu",
                           count, dest_size);
        return MGEN_ERROR_VALUE;
    }

    memset(dest, value, count);
    return MGEN_OK;
}

// Memory pool implementation
mgen_memory_pool_t* mgen_memory_pool_new(size_t initial_size) {
    if (initial_size == 0) {
        initial_size = 4096; // Default 4KB
    }

    mgen_memory_pool_t* pool = malloc(sizeof(mgen_memory_pool_t));
    if (!pool) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory pool");
        return NULL;
    }

    pool->data = malloc(initial_size);
    if (!pool->data) {
        free(pool);
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory pool data");
        return NULL;
    }

    pool->size = 0;
    pool->capacity = initial_size;
    pool->used = 0;

    return pool;
}

void* mgen_memory_pool_alloc(mgen_memory_pool_t* pool, size_t size) {
    if (!pool) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Memory pool is NULL");
        return NULL;
    }

    // Align size to pointer boundary
    size = (size + sizeof(void*) - 1) & ~(sizeof(void*) - 1);

    if (pool->used + size > pool->capacity) {
        // Grow pool
        size_t new_capacity = pool->capacity * 2;
        while (new_capacity < pool->used + size) {
            new_capacity *= 2;
        }

        char* new_data = realloc(pool->data, new_capacity);
        if (!new_data) {
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow memory pool");
            return NULL;
        }

        pool->data = new_data;
        pool->capacity = new_capacity;
    }

    void* ptr = pool->data + pool->used;
    pool->used += size;
    pool->size++;

    return ptr;
}

void mgen_memory_pool_reset(mgen_memory_pool_t* pool) {
    if (!pool) return;

    pool->used = 0;
    pool->size = 0;
}

void mgen_memory_pool_free(mgen_memory_pool_t* pool) {
    if (!pool) return;

    free(pool->data);
    free(pool);
}

// Scope allocator implementation
mgen_scope_allocator_t* mgen_scope_new(void) {
    mgen_scope_allocator_t* scope = malloc(sizeof(mgen_scope_allocator_t));
    if (!scope) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate scope allocator");
        return NULL;
    }

    scope->head = NULL;
    scope->count = 0;

    return scope;
}

void* mgen_scope_alloc(mgen_scope_allocator_t* scope, size_t size) {
    if (!scope) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Scope allocator is NULL");
        return NULL;
    }

    void* ptr = mgen_malloc(size);
    if (!ptr) return NULL;

    if (mgen_scope_register(scope, ptr) != MGEN_OK) {
        mgen_free(&ptr);
        return NULL;
    }

    return ptr;
}

mgen_error_t mgen_scope_register(mgen_scope_allocator_t* scope, void* ptr) {
    if (!scope) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Scope allocator is NULL");
        return MGEN_ERROR_VALUE;
    }

    if (!ptr) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Pointer is NULL");
        return MGEN_ERROR_VALUE;
    }

    alloc_entry_t* entry = malloc(sizeof(alloc_entry_t));
    if (!entry) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate scope entry");
        return MGEN_ERROR_MEMORY;
    }

    entry->ptr = ptr;
    entry->next = scope->head;
    scope->head = entry;
    scope->count++;

    return MGEN_OK;
}

void mgen_scope_free(mgen_scope_allocator_t* scope) {
    if (!scope) return;

    alloc_entry_t* current = scope->head;
    while (current) {
        alloc_entry_t* next = current->next;
        mgen_free(&current->ptr);
        free(current);
        current = next;
    }

    free(scope);
}

// Memory tracking functions
void mgen_memory_tracking_enable(void) {
    memory_tracking_enabled = 1;
    memset(&memory_stats, 0, sizeof(memory_stats));
}

void mgen_memory_tracking_disable(void) {
    memory_tracking_enabled = 0;
}

mgen_memory_stats_t mgen_get_memory_stats(void) {
    return memory_stats;
}

void mgen_print_memory_stats(void) {
    printf("Memory Statistics:\n");
    printf("  Total allocated: %zu bytes\n", memory_stats.total_allocated);
    printf("  Total freed: %zu bytes\n", memory_stats.total_freed);
    printf("  Currently allocated: %zu bytes\n", memory_stats.current_allocated);
    printf("  Peak allocated: %zu bytes\n", memory_stats.peak_allocated);
    printf("  Allocation count: %zu\n", memory_stats.allocation_count);
    printf("  Free count: %zu\n", memory_stats.free_count);
}

int mgen_check_memory_leaks(void) {
    return memory_stats.current_allocated > 0;
}

// Reference counting implementation
mgen_refcounted_t* mgen_refcounted_new(size_t data_size, void (*destructor)(void*)) {
    mgen_refcounted_t* obj = malloc(sizeof(mgen_refcounted_t) + data_size);
    if (!obj) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate reference counted object");
        return NULL;
    }

    obj->refcount = 1;
    obj->destructor = destructor;

    return obj;
}

mgen_refcounted_t* mgen_refcounted_retain(mgen_refcounted_t* obj) {
    if (!obj) return NULL;

    obj->refcount++;
    return obj;
}

void mgen_refcounted_release(mgen_refcounted_t* obj) {
    if (!obj) return;

    obj->refcount--;
    if (obj->refcount <= 0) {
        if (obj->destructor) {
            obj->destructor(obj->data);
        }
        free(obj);
    }
}

int mgen_refcounted_count(mgen_refcounted_t* obj) {
    return obj ? obj->refcount : 0;
}

void* mgen_refcounted_data(mgen_refcounted_t* obj) {
    return obj ? obj->data : NULL;
}

// Buffer implementation
mgen_buffer_t* mgen_buffer_new(size_t initial_capacity) {
    if (initial_capacity == 0) {
        initial_capacity = 256; // Default 256 bytes
    }

    mgen_buffer_t* buffer = malloc(sizeof(mgen_buffer_t));
    if (!buffer) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate buffer");
        return NULL;
    }

    buffer->data = malloc(initial_capacity);
    if (!buffer->data) {
        free(buffer);
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate buffer data");
        return NULL;
    }

    buffer->size = 0;
    buffer->capacity = initial_capacity;
    buffer->data[0] = '\0';

    return buffer;
}

mgen_error_t mgen_buffer_append(mgen_buffer_t* buffer, const char* data, size_t len) {
    if (!buffer || !data) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Buffer or data is NULL");
        return MGEN_ERROR_VALUE;
    }

    if (buffer->size + len + 1 > buffer->capacity) {
        size_t new_capacity = buffer->capacity;
        while (new_capacity < buffer->size + len + 1) {
            new_capacity *= 2;
        }

        char* new_data = realloc(buffer->data, new_capacity);
        if (!new_data) {
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow buffer");
            return MGEN_ERROR_MEMORY;
        }

        buffer->data = new_data;
        buffer->capacity = new_capacity;
    }

    memcpy(buffer->data + buffer->size, data, len);
    buffer->size += len;
    buffer->data[buffer->size] = '\0';

    return MGEN_OK;
}

mgen_error_t mgen_buffer_append_str(mgen_buffer_t* buffer, const char* str) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return MGEN_ERROR_VALUE;
    }

    return mgen_buffer_append(buffer, str, strlen(str));
}

mgen_error_t mgen_buffer_append_fmt(mgen_buffer_t* buffer, const char* format, ...) {
    if (!buffer || !format) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Buffer or format is NULL");
        return MGEN_ERROR_VALUE;
    }

    va_list args;
    va_start(args, format);

    // Calculate required size
    va_list args_copy;
    va_copy(args_copy, args);
    int len = vsnprintf(NULL, 0, format, args_copy);
    va_end(args_copy);

    if (len < 0) {
        va_end(args);
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid format string");
        return MGEN_ERROR_VALUE;
    }

    // Ensure buffer has enough space
    if (buffer->size + len + 1 > buffer->capacity) {
        size_t new_capacity = buffer->capacity;
        while (new_capacity < buffer->size + len + 1) {
            new_capacity *= 2;
        }

        char* new_data = realloc(buffer->data, new_capacity);
        if (!new_data) {
            va_end(args);
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow buffer");
            return MGEN_ERROR_MEMORY;
        }

        buffer->data = new_data;
        buffer->capacity = new_capacity;
    }

    vsnprintf(buffer->data + buffer->size, len + 1, format, args);
    buffer->size += len;
    va_end(args);

    return MGEN_OK;
}

const char* mgen_buffer_cstr(mgen_buffer_t* buffer) {
    return buffer ? buffer->data : NULL;
}

size_t mgen_buffer_size(mgen_buffer_t* buffer) {
    return buffer ? buffer->size : 0;
}

void mgen_buffer_clear(mgen_buffer_t* buffer) {
    if (!buffer) return;

    buffer->size = 0;
    if (buffer->data) {
        buffer->data[0] = '\0';
    }
}

void mgen_buffer_free(mgen_buffer_t* buffer) {
    if (!buffer) return;

    free(buffer->data);
    free(buffer);
}