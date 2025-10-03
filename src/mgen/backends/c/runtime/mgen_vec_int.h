/**
 * Simple dynamic array for integers
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_VEC_INT_H
#define MGEN_VEC_INT_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Dynamic integer array structure (STC-compatible naming)
typedef struct {
    int* data;           // Array data
    size_t size;         // Number of elements
    size_t capacity;     // Allocated capacity
} vec_int;

/**
 * Create a new integer vector
 * Initial capacity defaults to 8
 */
vec_int vec_int_init(void);

/**
 * Append an element to the end (STC-compatible)
 * No return value - for compatibility with STC vec_int_push(&vec, value)
 */
void vec_int_push(vec_int* vec, int value);

/**
 * Get pointer to element at index (STC-compatible)
 * Returns pointer to element if valid, NULL if out of bounds
 */
int* vec_int_at(vec_int* vec, size_t index);

/**
 * Get number of elements
 */
size_t vec_int_size(const vec_int* vec);

/**
 * Get allocated capacity
 */
size_t vec_int_capacity(const vec_int* vec);

/**
 * Remove last element
 */
void vec_int_pop(vec_int* vec);

/**
 * Clear all elements (keep capacity)
 */
void vec_int_clear(vec_int* vec);

/**
 * Free all memory (STC-compatible drop function)
 */
void vec_int_drop(vec_int* vec);

/**
 * Check if vector is empty
 */
bool vec_int_empty(const vec_int* vec);

/**
 * Reserve capacity
 */
void vec_int_reserve(vec_int* vec, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_VEC_INT_H
