/**
 * Dynamic array of C strings (char*)
 * Clean, type-safe implementation for code generation
 * STC-compatible naming: vec_cstr
 */

#ifndef MGEN_VEC_CSTR_H
#define MGEN_VEC_CSTR_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Dynamic array of C strings structure
typedef struct {
    char** data;         // Array of string pointers
    size_t size;         // Number of strings
    size_t capacity;     // Allocated capacity
} vec_cstr;

/**
 * Create a new string vector
 * Initial capacity defaults to 8
 */
vec_cstr vec_cstr_init(void);

/**
 * Append a string to the end (STC-compatible)
 * Makes a copy of the string (uses strdup)
 * No return value - for compatibility with STC vec_cstr_push(&vec, str)
 */
void vec_cstr_push(vec_cstr* vec, const char* str);

/**
 * Get pointer to string at index (STC-compatible)
 * Returns pointer to string pointer if valid, NULL if out of bounds
 */
char** vec_cstr_at(vec_cstr* vec, size_t index);

/**
 * Get number of strings
 */
size_t vec_cstr_size(const vec_cstr* vec);

/**
 * Get allocated capacity
 */
size_t vec_cstr_capacity(const vec_cstr* vec);

/**
 * Remove last string (and free its memory)
 */
void vec_cstr_pop(vec_cstr* vec);

/**
 * Clear all strings (free each string's memory)
 */
void vec_cstr_clear(vec_cstr* vec);

/**
 * Free all memory (STC-compatible drop function)
 * Frees each string and the array itself
 */
void vec_cstr_drop(vec_cstr* vec);

/**
 * Check if vector is empty
 */
bool vec_cstr_empty(const vec_cstr* vec);

/**
 * Reserve capacity
 */
void vec_cstr_reserve(vec_cstr* vec, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_VEC_CSTR_H
