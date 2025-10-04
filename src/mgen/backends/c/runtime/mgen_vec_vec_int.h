/**
 * Dynamic array of integer vectors (2D arrays)
 * Clean, type-safe implementation for code generation
 * STC-compatible naming: vec_vec_int
 */

#ifndef MGEN_VEC_VEC_INT_H
#define MGEN_VEC_VEC_INT_H

#include <stddef.h>
#include <stdbool.h>
#include "mgen_vec_int.h"

#ifdef __cplusplus
extern "C" {
#endif

// Dynamic array of vec_int (2D integer array structure)
typedef struct {
    vec_int* data;       // Array of vec_int structs
    size_t size;         // Number of rows
    size_t capacity;     // Allocated capacity
} vec_vec_int;

/**
 * Create a new 2D integer vector
 * Initial capacity defaults to 8
 */
vec_vec_int vec_vec_int_init(void);

/**
 * Append a row (vec_int) to the end (STC-compatible)
 * Takes ownership of the vec_int and copies it
 */
void vec_vec_int_push(vec_vec_int* vec, vec_int row);

/**
 * Get pointer to row at index (STC-compatible)
 * Returns pointer to vec_int if valid, NULL if out of bounds
 */
vec_int* vec_vec_int_at(vec_vec_int* vec, size_t index);

/**
 * Get number of rows
 */
size_t vec_vec_int_size(const vec_vec_int* vec);

/**
 * Get allocated capacity
 */
size_t vec_vec_int_capacity(const vec_vec_int* vec);

/**
 * Remove last row (and free its memory)
 */
void vec_vec_int_pop(vec_vec_int* vec);

/**
 * Clear all rows (free each row's memory)
 */
void vec_vec_int_clear(vec_vec_int* vec);

/**
 * Free all memory (STC-compatible drop function)
 * Calls vec_int_drop on each row
 */
void vec_vec_int_drop(vec_vec_int* vec);

/**
 * Check if 2D vector is empty
 */
bool vec_vec_int_empty(const vec_vec_int* vec);

/**
 * Reserve capacity for rows
 */
void vec_vec_int_reserve(vec_vec_int* vec, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_VEC_VEC_INT_H
