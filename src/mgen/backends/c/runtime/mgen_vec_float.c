/**
 * Simple dynamic array for floats - Implementation
 * STC-compatible naming for drop-in replacement
 */

#include "mgen_vec_float.h"
#include "mgen_error_handling.h"
#include <stdlib.h>
#include <string.h>

#define DEFAULT_CAPACITY 8
#define GROWTH_FACTOR 2

vec_float vec_float_init(void) {
    vec_float vec;
    vec.capacity = DEFAULT_CAPACITY;
    vec.size = 0;
    vec.data = malloc(DEFAULT_CAPACITY * sizeof(float));
    if (!vec.data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate float vector");
        vec.capacity = 0;
    }
    return vec;
}

static void vec_float_grow(vec_float* vec) {
    // Handle first allocation if capacity is 0
    size_t new_capacity = (vec->capacity == 0) ? DEFAULT_CAPACITY : vec->capacity * GROWTH_FACTOR;
    float* new_data = realloc(vec->data, new_capacity * sizeof(float));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow float vector");
        return;
    }
    vec->data = new_data;
    vec->capacity = new_capacity;
}

void vec_float_push(vec_float* vec, float value) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL float vector");
        return;
    }

    if (vec->size >= vec->capacity) {
        vec_float_grow(vec);
    }

    vec->data[vec->size++] = value;
}

float* vec_float_at(vec_float* vec, size_t index) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL float vector");
        return NULL;
    }

    if (index >= vec->size) {
        MGEN_SET_ERROR(MGEN_ERROR_INDEX, "Index out of bounds");
        return NULL;
    }

    return &vec->data[index];
}

size_t vec_float_size(const vec_float* vec) {
    return vec ? vec->size : 0;
}

size_t vec_float_capacity(const vec_float* vec) {
    return vec ? vec->capacity : 0;
}

void vec_float_pop(vec_float* vec) {
    if (!vec || vec->size == 0) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Empty or NULL float vector");
        return;
    }
    vec->size--;
}

void vec_float_clear(vec_float* vec) {
    if (vec) {
        vec->size = 0;
    }
}

void vec_float_drop(vec_float* vec) {
    if (!vec) {
        return;
    }
    free(vec->data);
    vec->data = NULL;
    vec->size = 0;
    vec->capacity = 0;
}

bool vec_float_empty(const vec_float* vec) {
    return !vec || vec->size == 0;
}

void vec_float_reserve(vec_float* vec, size_t new_capacity) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL float vector");
        return;
    }

    if (new_capacity <= vec->capacity) {
        return; // Already have enough capacity
    }

    float* new_data = realloc(vec->data, new_capacity * sizeof(float));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to reserve capacity");
        return;
    }

    vec->data = new_data;
    vec->capacity = new_capacity;
}
