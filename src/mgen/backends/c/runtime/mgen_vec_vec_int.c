/**
 * Dynamic array of integer vectors (2D arrays) - Implementation
 * STC-compatible naming for drop-in replacement
 */

#include "mgen_vec_vec_int.h"
#include "mgen_error_handling.h"
#include <stdlib.h>
#include <string.h>

#define DEFAULT_CAPACITY 8
#define GROWTH_FACTOR 2

vec_vec_int vec_vec_int_init(void) {
    vec_vec_int vec;
    vec.capacity = DEFAULT_CAPACITY;
    vec.size = 0;
    vec.data = malloc(DEFAULT_CAPACITY * sizeof(vec_int));
    if (!vec.data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate 2D vector");
        vec.capacity = 0;
    }
    return vec;
}

static void vec_vec_int_grow(vec_vec_int* vec) {
    // Handle first allocation if capacity is 0
    size_t new_capacity = (vec->capacity == 0) ? DEFAULT_CAPACITY : vec->capacity * GROWTH_FACTOR;
    vec_int* new_data = realloc(vec->data, new_capacity * sizeof(vec_int));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow 2D vector");
        return;
    }
    vec->data = new_data;
    vec->capacity = new_capacity;
}

void vec_vec_int_push(vec_vec_int* vec, vec_int row) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL 2D vector");
        return;
    }

    if (vec->size >= vec->capacity) {
        vec_vec_int_grow(vec);
    }

    // Copy the row into the array
    vec->data[vec->size++] = row;
}

vec_int* vec_vec_int_at(vec_vec_int* vec, size_t index) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL 2D vector");
        return NULL;
    }

    if (index >= vec->size) {
        MGEN_SET_ERROR(MGEN_ERROR_INDEX, "Index out of bounds");
        return NULL;
    }

    return &vec->data[index];
}

size_t vec_vec_int_size(const vec_vec_int* vec) {
    return vec ? vec->size : 0;
}

size_t vec_vec_int_capacity(const vec_vec_int* vec) {
    return vec ? vec->capacity : 0;
}

void vec_vec_int_pop(vec_vec_int* vec) {
    if (!vec || vec->size == 0) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Empty or NULL 2D vector");
        return;
    }

    // Drop the last row's memory before removing it
    vec_int_drop(&vec->data[vec->size - 1]);
    vec->size--;
}

void vec_vec_int_clear(vec_vec_int* vec) {
    if (!vec) {
        return;
    }

    // Drop each row's memory
    for (size_t i = 0; i < vec->size; i++) {
        vec_int_drop(&vec->data[i]);
    }

    vec->size = 0;
}

void vec_vec_int_drop(vec_vec_int* vec) {
    if (!vec) {
        return;
    }

    // Drop each row's memory
    for (size_t i = 0; i < vec->size; i++) {
        vec_int_drop(&vec->data[i]);
    }

    free(vec->data);
    vec->data = NULL;
    vec->size = 0;
    vec->capacity = 0;
}

bool vec_vec_int_empty(const vec_vec_int* vec) {
    return !vec || vec->size == 0;
}

void vec_vec_int_reserve(vec_vec_int* vec, size_t new_capacity) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL 2D vector");
        return;
    }

    if (new_capacity <= vec->capacity) {
        return; // Already have enough capacity
    }

    vec_int* new_data = realloc(vec->data, new_capacity * sizeof(vec_int));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to reserve capacity");
        return;
    }

    vec->data = new_data;
    vec->capacity = new_capacity;
}
