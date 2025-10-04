/**
 * Simple dynamic array for doubles - Implementation
 * STC-compatible naming for drop-in replacement
 */

#include "mgen_vec_double.h"
#include "mgen_error_handling.h"
#include <stdlib.h>
#include <string.h>

#define DEFAULT_CAPACITY 8
#define GROWTH_FACTOR 2

vec_double vec_double_init(void) {
    vec_double vec;
    vec.capacity = DEFAULT_CAPACITY;
    vec.size = 0;
    vec.data = malloc(DEFAULT_CAPACITY * sizeof(double));
    if (!vec.data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate double vector");
        vec.capacity = 0;
    }
    return vec;
}

static void vec_double_grow(vec_double* vec) {
    // Handle first allocation if capacity is 0
    size_t new_capacity = (vec->capacity == 0) ? DEFAULT_CAPACITY : vec->capacity * GROWTH_FACTOR;
    double* new_data = realloc(vec->data, new_capacity * sizeof(double));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow double vector");
        return;
    }
    vec->data = new_data;
    vec->capacity = new_capacity;
}

void vec_double_push(vec_double* vec, double value) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL double vector");
        return;
    }

    if (vec->size >= vec->capacity) {
        vec_double_grow(vec);
    }

    vec->data[vec->size++] = value;
}

double* vec_double_at(vec_double* vec, size_t index) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL double vector");
        return NULL;
    }

    if (index >= vec->size) {
        MGEN_SET_ERROR(MGEN_ERROR_INDEX, "Index out of bounds");
        return NULL;
    }

    return &vec->data[index];
}

size_t vec_double_size(const vec_double* vec) {
    return vec ? vec->size : 0;
}

size_t vec_double_capacity(const vec_double* vec) {
    return vec ? vec->capacity : 0;
}

void vec_double_pop(vec_double* vec) {
    if (!vec || vec->size == 0) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Empty or NULL double vector");
        return;
    }
    vec->size--;
}

void vec_double_clear(vec_double* vec) {
    if (vec) {
        vec->size = 0;
    }
}

void vec_double_drop(vec_double* vec) {
    if (!vec) {
        return;
    }
    free(vec->data);
    vec->data = NULL;
    vec->size = 0;
    vec->capacity = 0;
}

bool vec_double_empty(const vec_double* vec) {
    return !vec || vec->size == 0;
}

void vec_double_reserve(vec_double* vec, size_t new_capacity) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL double vector");
        return;
    }

    if (new_capacity <= vec->capacity) {
        return; // Already have enough capacity
    }

    double* new_data = realloc(vec->data, new_capacity * sizeof(double));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to reserve capacity");
        return;
    }

    vec->data = new_data;
    vec->capacity = new_capacity;
}
