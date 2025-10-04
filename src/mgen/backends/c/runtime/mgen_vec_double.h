/**
 * Simple dynamic array for doubles
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_VEC_DOUBLE_H
#define MGEN_VEC_DOUBLE_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Dynamic double array structure (STC-compatible naming)
typedef struct {
    double* data;        // Array data
    size_t size;         // Number of elements
    size_t capacity;     // Allocated capacity
} vec_double;

/**
 * Create a new double vector
 * Initial capacity defaults to 8
 */
vec_double vec_double_init(void);

/**
 * Append an element to the end (STC-compatible)
 */
void vec_double_push(vec_double* vec, double value);

/**
 * Get pointer to element at index (STC-compatible)
 */
double* vec_double_at(vec_double* vec, size_t index);

/**
 * Get number of elements
 */
size_t vec_double_size(const vec_double* vec);

/**
 * Get allocated capacity
 */
size_t vec_double_capacity(const vec_double* vec);

/**
 * Remove last element
 */
void vec_double_pop(vec_double* vec);

/**
 * Clear all elements (keep capacity)
 */
void vec_double_clear(vec_double* vec);

/**
 * Free all memory (STC-compatible drop function)
 */
void vec_double_drop(vec_double* vec);

/**
 * Check if vector is empty
 */
bool vec_double_empty(const vec_double* vec);

/**
 * Reserve capacity
 */
void vec_double_reserve(vec_double* vec, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_VEC_DOUBLE_H
