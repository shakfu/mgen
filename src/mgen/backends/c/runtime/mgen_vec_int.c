/**
 * Simple dynamic array for integers - Implementation
 * STC-compatible naming for drop-in replacement
 */

#include "mgen_vec_int.h"
#include "mgen_error_handling.h"
#include <stdlib.h>
#include <string.h>

#define DEFAULT_CAPACITY 8
#define GROWTH_FACTOR 2

vec_int vec_int_init(void) {
    vec_int vec;
    vec.capacity = DEFAULT_CAPACITY;
    vec.size = 0;
    vec.data = malloc(DEFAULT_CAPACITY * sizeof(int));
    if (!vec.data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate vector");
        vec.capacity = 0;
    }
    return vec;
}

static void vec_int_grow(vec_int* vec) {
    // Handle first allocation if capacity is 0
    size_t new_capacity = (vec->capacity == 0) ? DEFAULT_CAPACITY : vec->capacity * GROWTH_FACTOR;
    int* new_data = realloc(vec->data, new_capacity * sizeof(int));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to grow vector");
        return;
    }
    vec->data = new_data;
    vec->capacity = new_capacity;
}

void vec_int_push(vec_int* vec, int value) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL vector");
        return;
    }

    if (vec->size >= vec->capacity) {
        vec_int_grow(vec);
    }

    vec->data[vec->size++] = value;
}

int* vec_int_at(vec_int* vec, size_t index) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL vector");
        return NULL;
    }

    if (index >= vec->size) {
        MGEN_SET_ERROR(MGEN_ERROR_INDEX, "Index out of bounds");
        return NULL;
    }

    return &vec->data[index];
}

size_t vec_int_size(const vec_int* vec) {
    return vec ? vec->size : 0;
}

size_t vec_int_capacity(const vec_int* vec) {
    return vec ? vec->capacity : 0;
}

void vec_int_pop(vec_int* vec) {
    if (!vec || vec->size == 0) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Empty or NULL vector");
        return;
    }
    vec->size--;
}

void vec_int_clear(vec_int* vec) {
    if (vec) {
        vec->size = 0;
    }
}

void vec_int_drop(vec_int* vec) {
    if (!vec) {
        return;
    }
    free(vec->data);
    vec->data = NULL;
    vec->size = 0;
    vec->capacity = 0;
}

bool vec_int_empty(const vec_int* vec) {
    return !vec || vec->size == 0;
}

void vec_int_reserve(vec_int* vec, size_t new_capacity) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL vector");
        return;
    }

    if (new_capacity <= vec->capacity) {
        return; // Already have enough capacity
    }

    int* new_data = realloc(vec->data, new_capacity * sizeof(int));
    if (!new_data) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to reserve capacity");
        return;
    }

    vec->data = new_data;
    vec->capacity = new_capacity;
}
