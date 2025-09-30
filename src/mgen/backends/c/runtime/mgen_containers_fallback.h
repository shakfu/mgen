/**
 * MGen Runtime Library - Fallback Container Implementations
 *
 * Provides basic container implementations when STC is not available.
 * These containers are generic dynamic arrays with size/capacity tracking.
 */

#ifndef MGEN_CONTAINERS_FALLBACK_H
#define MGEN_CONTAINERS_FALLBACK_H

#include <stddef.h>
#include <stdbool.h>
#include "mgen_error_handling.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Generic dynamic array structure
 * This is used as a fallback when STC is not available
 */
typedef struct mgen_dyn_array {
    void* data;           // Pointer to array data
    size_t size;          // Number of elements
    size_t capacity;      // Allocated capacity
    size_t element_size;  // Size of each element in bytes
} mgen_dyn_array_t;

/**
 * Create a new dynamic array
 *
 * @param element_size Size of each element in bytes
 * @param initial_capacity Initial capacity (default: 8 if 0)
 * @return Pointer to new array or NULL on failure
 */
mgen_dyn_array_t* mgen_dyn_array_new(size_t element_size, size_t initial_capacity);

/**
 * Free a dynamic array
 *
 * @param array Array to free
 */
void mgen_dyn_array_free(mgen_dyn_array_t* array);

/**
 * Append an element to the end of the array
 *
 * @param array Array to modify
 * @param element Pointer to element to append
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_append(mgen_dyn_array_t* array, const void* element);

/**
 * Insert an element at a specific index
 *
 * @param array Array to modify
 * @param index Index to insert at
 * @param element Pointer to element to insert
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_insert(mgen_dyn_array_t* array, size_t index, const void* element);

/**
 * Remove an element at a specific index
 *
 * @param array Array to modify
 * @param index Index to remove
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_remove(mgen_dyn_array_t* array, size_t index);

/**
 * Get a pointer to an element at a specific index
 *
 * @param array Array to access
 * @param index Index to access
 * @return Pointer to element or NULL if out of bounds
 */
void* mgen_dyn_array_get(const mgen_dyn_array_t* array, size_t index);

/**
 * Set an element at a specific index
 *
 * @param array Array to modify
 * @param index Index to set
 * @param element Pointer to element data
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_set(mgen_dyn_array_t* array, size_t index, const void* element);

/**
 * Get the size of the array
 *
 * @param array Array to query
 * @return Number of elements in the array
 */
size_t mgen_dyn_array_size(const mgen_dyn_array_t* array);

/**
 * Get the capacity of the array
 *
 * @param array Array to query
 * @return Allocated capacity of the array
 */
size_t mgen_dyn_array_capacity(const mgen_dyn_array_t* array);

/**
 * Clear all elements from the array
 *
 * @param array Array to clear
 */
void mgen_dyn_array_clear(mgen_dyn_array_t* array);

/**
 * Check if the array contains an element
 * Uses memcmp for comparison - suitable for primitive types
 *
 * @param array Array to search
 * @param element Pointer to element to find
 * @return true if element is found, false otherwise
 */
bool mgen_dyn_array_contains(const mgen_dyn_array_t* array, const void* element);

/**
 * Reserve capacity for the array
 *
 * @param array Array to modify
 * @param new_capacity Minimum capacity to reserve
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_reserve(mgen_dyn_array_t* array, size_t new_capacity);

/**
 * Shrink array capacity to fit current size
 *
 * @param array Array to shrink
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_shrink_to_fit(mgen_dyn_array_t* array);

/**
 * Get the last element in the array
 *
 * @param array Array to access
 * @return Pointer to last element or NULL if empty
 */
void* mgen_dyn_array_back(const mgen_dyn_array_t* array);

/**
 * Remove the last element from the array
 *
 * @param array Array to modify
 * @return MGEN_OK on success, error code on failure
 */
mgen_error_t mgen_dyn_array_pop_back(mgen_dyn_array_t* array);

/**
 * Check if the array is empty
 *
 * @param array Array to check
 * @return true if empty, false otherwise
 */
bool mgen_dyn_array_empty(const mgen_dyn_array_t* array);

/**
 * Macros for type-safe array operations
 */

// Create typed dynamic array wrapper
#define MGEN_DYN_ARRAY_TYPE(type) \
    typedef struct { \
        mgen_dyn_array_t* impl; \
    } mgen_dyn_array_##type##_t

// Initialize typed array
#define MGEN_DYN_ARRAY_INIT(type, initial_capacity) \
    { .impl = mgen_dyn_array_new(sizeof(type), (initial_capacity)) }

// Append to typed array
#define MGEN_DYN_ARRAY_APPEND(array, value) \
    do { \
        __typeof__(value) __temp = (value); \
        mgen_dyn_array_append((array)->impl, &__temp); \
    } while(0)

// Get from typed array
#define MGEN_DYN_ARRAY_GET(array, type, index) \
    ((type*)mgen_dyn_array_get((array)->impl, (index)))

// Size of typed array
#define MGEN_DYN_ARRAY_SIZE(array) \
    mgen_dyn_array_size((array)->impl)

// Clear typed array
#define MGEN_DYN_ARRAY_CLEAR(array) \
    mgen_dyn_array_clear((array)->impl)

// Free typed array
#define MGEN_DYN_ARRAY_FREE(array) \
    do { \
        if ((array)->impl) { \
            mgen_dyn_array_free((array)->impl); \
            (array)->impl = NULL; \
        } \
    } while(0)

#ifdef __cplusplus
}
#endif

#endif // MGEN_CONTAINERS_FALLBACK_H
