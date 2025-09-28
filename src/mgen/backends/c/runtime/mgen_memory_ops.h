/**
 * MGen Runtime Library - Memory Management Utilities
 *
 * Provides safe memory management utilities for generated C code.
 * These functions handle error checking and automatic cleanup.
 */

#ifndef MGEN_MEMORY_OPS_H
#define MGEN_MEMORY_OPS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mgen_error_handling.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Safe memory allocation with error handling
 */
void* mgen_malloc(size_t size);

/**
 * Safe memory reallocation with error handling
 */
void* mgen_realloc(void* ptr, size_t new_size);

/**
 * Safe memory allocation for arrays with overflow checking
 */
void* mgen_calloc(size_t count, size_t size);

/**
 * Safe memory deallocation (sets pointer to NULL)
 */
void mgen_free(void** ptr);

/**
 * Safe memory copy with bounds checking
 */
mgen_error_t mgen_memcpy_safe(void* dest, size_t dest_size,
                             const void* src, size_t src_size);

/**
 * Safe memory move with bounds checking
 */
mgen_error_t mgen_memmove_safe(void* dest, size_t dest_size,
                              const void* src, size_t src_size);

/**
 * Safe memory set with bounds checking
 */
mgen_error_t mgen_memset_safe(void* dest, int value, size_t count, size_t dest_size);

/**
 * Memory pool for efficient allocation/deallocation
 */
typedef struct mgen_memory_pool mgen_memory_pool_t;

/**
 * Create a new memory pool
 */
mgen_memory_pool_t* mgen_memory_pool_new(size_t initial_size);

/**
 * Allocate from memory pool
 */
void* mgen_memory_pool_alloc(mgen_memory_pool_t* pool, size_t size);

/**
 * Reset memory pool (deallocates all at once)
 */
void mgen_memory_pool_reset(mgen_memory_pool_t* pool);

/**
 * Free memory pool
 */
void mgen_memory_pool_free(mgen_memory_pool_t* pool);

/**
 * Automatic memory management with scope-based cleanup
 */
typedef struct mgen_scope_allocator mgen_scope_allocator_t;

/**
 * Create a new scope allocator
 */
mgen_scope_allocator_t* mgen_scope_new(void);

/**
 * Allocate memory that will be automatically freed when scope ends
 */
void* mgen_scope_alloc(mgen_scope_allocator_t* scope, size_t size);

/**
 * Register existing pointer for automatic cleanup
 */
mgen_error_t mgen_scope_register(mgen_scope_allocator_t* scope, void* ptr);

/**
 * Free all allocations in scope
 */
void mgen_scope_free(mgen_scope_allocator_t* scope);

/**
 * Memory debugging and leak detection
 */
typedef struct mgen_memory_stats {
    size_t total_allocated;
    size_t total_freed;
    size_t current_allocated;
    size_t peak_allocated;
    size_t allocation_count;
    size_t free_count;
} mgen_memory_stats_t;

/**
 * Enable memory tracking
 */
void mgen_memory_tracking_enable(void);

/**
 * Disable memory tracking
 */
void mgen_memory_tracking_disable(void);

/**
 * Get current memory statistics
 */
mgen_memory_stats_t mgen_get_memory_stats(void);

/**
 * Print memory statistics
 */
void mgen_print_memory_stats(void);

/**
 * Check for memory leaks
 */
int mgen_check_memory_leaks(void);

/**
 * Reference counting utilities
 */
typedef struct mgen_refcounted {
    int refcount;
    void (*destructor)(void* data);
    char data[];
} mgen_refcounted_t;

/**
 * Create reference counted object
 */
mgen_refcounted_t* mgen_refcounted_new(size_t data_size, void (*destructor)(void*));

/**
 * Increment reference count
 */
mgen_refcounted_t* mgen_refcounted_retain(mgen_refcounted_t* obj);

/**
 * Decrement reference count (frees if reaches 0)
 */
void mgen_refcounted_release(mgen_refcounted_t* obj);

/**
 * Get reference count
 */
int mgen_refcounted_count(mgen_refcounted_t* obj);

/**
 * Get data pointer from reference counted object
 */
void* mgen_refcounted_data(mgen_refcounted_t* obj);

/**
 * Buffer management for string operations
 */
typedef struct mgen_buffer {
    char* data;
    size_t size;
    size_t capacity;
} mgen_buffer_t;

/**
 * Create a new dynamic buffer
 */
mgen_buffer_t* mgen_buffer_new(size_t initial_capacity);

/**
 * Append data to buffer
 */
mgen_error_t mgen_buffer_append(mgen_buffer_t* buffer, const char* data, size_t len);

/**
 * Append string to buffer
 */
mgen_error_t mgen_buffer_append_str(mgen_buffer_t* buffer, const char* str);

/**
 * Append formatted string to buffer
 */
mgen_error_t mgen_buffer_append_fmt(mgen_buffer_t* buffer, const char* format, ...);

/**
 * Get buffer data as C string
 */
const char* mgen_buffer_cstr(mgen_buffer_t* buffer);

/**
 * Get buffer size
 */
size_t mgen_buffer_size(mgen_buffer_t* buffer);

/**
 * Clear buffer (reset size to 0)
 */
void mgen_buffer_clear(mgen_buffer_t* buffer);

/**
 * Free buffer
 */
void mgen_buffer_free(mgen_buffer_t* buffer);

/**
 * RAII-style cleanup macros
 */
#define MGEN_SCOPE_BEGIN() \
    do { \
        mgen_scope_allocator_t* __scope = mgen_scope_new(); \
        if (!__scope) break;

#define MGEN_SCOPE_END() \
        mgen_scope_free(__scope); \
    } while(0)

#define MGEN_SCOPE_ALLOC(size) \
    mgen_scope_alloc(__scope, (size))

#define MGEN_SCOPE_REGISTER(ptr) \
    mgen_scope_register(__scope, (ptr))

/**
 * Memory pool macros for common patterns
 */
#define MGEN_POOL_BEGIN(size) \
    do { \
        mgen_memory_pool_t* __pool = mgen_memory_pool_new(size); \
        if (!__pool) break;

#define MGEN_POOL_END() \
        mgen_memory_pool_free(__pool); \
    } while(0)

#define MGEN_POOL_ALLOC(size) \
    mgen_memory_pool_alloc(__pool, (size))

#ifdef __cplusplus
}
#endif

#endif // MGEN_MEMORY_OPS_H