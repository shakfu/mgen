/**
 * Simple dynamic array for floats
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_VEC_FLOAT_H
#define MGEN_VEC_FLOAT_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Dynamic float array structure (STC-compatible naming)
typedef struct {
    float* data;         // Array data
    size_t size;         // Number of elements
    size_t capacity;     // Allocated capacity
} vec_float;

/**
 * Create a new float vector
 * Initial capacity defaults to 8
 */
vec_float vec_float_init(void);

/**
 * Append an element to the end (STC-compatible)
 */
void vec_float_push(vec_float* vec, float value);

/**
 * Get pointer to element at index (STC-compatible)
 */
float* vec_float_at(vec_float* vec, size_t index);

/**
 * Get number of elements
 */
size_t vec_float_size(const vec_float* vec);

/**
 * Get allocated capacity
 */
size_t vec_float_capacity(const vec_float* vec);

/**
 * Remove last element
 */
void vec_float_pop(vec_float* vec);

/**
 * Clear all elements (keep capacity)
 */
void vec_float_clear(vec_float* vec);

/**
 * Free all memory (STC-compatible drop function)
 */
void vec_float_drop(vec_float* vec);

/**
 * Check if vector is empty
 */
bool vec_float_empty(const vec_float* vec);

/**
 * Reserve capacity
 */
void vec_float_reserve(vec_float* vec, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_VEC_FLOAT_H
