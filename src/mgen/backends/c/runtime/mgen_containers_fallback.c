/**
 * MGen Runtime Library - Fallback Container Implementations
 *
 * Implementation of generic dynamic arrays for use when STC is not available.
 */

#include "mgen_containers_fallback.h"
#include "mgen_memory_ops.h"
#include <string.h>
#include <stdlib.h>

// Default initial capacity for dynamic arrays
#define MGEN_DYN_ARRAY_DEFAULT_CAPACITY 8

// Growth factor for dynamic arrays (multiply by 1.5)
#define MGEN_DYN_ARRAY_GROWTH_FACTOR(cap) ((cap) + (cap) / 2)

mgen_dyn_array_t* mgen_dyn_array_new(size_t element_size, size_t initial_capacity) {
    if (element_size == 0) {
        mgen_handle_error(MGEN_ERROR_INVALID_ARG, "Element size cannot be zero");
        return NULL;
    }

    mgen_dyn_array_t* array = (mgen_dyn_array_t*)malloc(sizeof(mgen_dyn_array_t));
    if (!array) {
        mgen_handle_error(MGEN_ERROR_MEMORY, "Failed to allocate dynamic array");
        return NULL;
    }

    if (initial_capacity == 0) {
        initial_capacity = MGEN_DYN_ARRAY_DEFAULT_CAPACITY;
    }

    array->element_size = element_size;
    array->size = 0;
    array->capacity = initial_capacity;
    array->data = malloc(element_size * initial_capacity);

    if (!array->data) {
        free(array);
        mgen_handle_error(MGEN_ERROR_MEMORY, "Failed to allocate array data");
        return NULL;
    }

    return array;
}

void mgen_dyn_array_free(mgen_dyn_array_t* array) {
    if (array) {
        if (array->data) {
            free(array->data);
        }
        free(array);
    }
}

mgen_error_t mgen_dyn_array_reserve(mgen_dyn_array_t* array, size_t new_capacity) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (new_capacity <= array->capacity) {
        return MGEN_OK; // Already have enough capacity
    }

    void* new_data = realloc(array->data, array->element_size * new_capacity);
    if (!new_data) {
        return mgen_handle_error(MGEN_ERROR_MEMORY, "Failed to reserve array capacity");
    }

    array->data = new_data;
    array->capacity = new_capacity;
    return MGEN_OK;
}

mgen_error_t mgen_dyn_array_append(mgen_dyn_array_t* array, const void* element) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (!element) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Element is NULL");
    }

    // Grow array if needed
    if (array->size >= array->capacity) {
        size_t new_capacity = MGEN_DYN_ARRAY_GROWTH_FACTOR(array->capacity);
        if (new_capacity <= array->capacity) {
            new_capacity = array->capacity + 1; // Handle edge case
        }

        mgen_error_t result = mgen_dyn_array_reserve(array, new_capacity);
        if (result != MGEN_OK) {
            return result;
        }
    }

    // Copy element to end of array
    void* dest = (char*)array->data + (array->size * array->element_size);
    memcpy(dest, element, array->element_size);
    array->size++;

    return MGEN_OK;
}

mgen_error_t mgen_dyn_array_insert(mgen_dyn_array_t* array, size_t index, const void* element) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (!element) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Element is NULL");
    }

    if (index > array->size) {
        return mgen_handle_error(MGEN_ERROR_OUT_OF_BOUNDS, "Insert index out of bounds");
    }

    // Grow array if needed
    if (array->size >= array->capacity) {
        size_t new_capacity = MGEN_DYN_ARRAY_GROWTH_FACTOR(array->capacity);
        mgen_error_t result = mgen_dyn_array_reserve(array, new_capacity);
        if (result != MGEN_OK) {
            return result;
        }
    }

    // Move elements after insertion point
    if (index < array->size) {
        void* src = (char*)array->data + (index * array->element_size);
        void* dest = (char*)array->data + ((index + 1) * array->element_size);
        size_t move_size = (array->size - index) * array->element_size;
        memmove(dest, src, move_size);
    }

    // Insert new element
    void* dest = (char*)array->data + (index * array->element_size);
    memcpy(dest, element, array->element_size);
    array->size++;

    return MGEN_OK;
}

mgen_error_t mgen_dyn_array_remove(mgen_dyn_array_t* array, size_t index) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (index >= array->size) {
        return mgen_handle_error(MGEN_ERROR_OUT_OF_BOUNDS, "Remove index out of bounds");
    }

    // Move elements after removal point
    if (index < array->size - 1) {
        void* dest = (char*)array->data + (index * array->element_size);
        void* src = (char*)array->data + ((index + 1) * array->element_size);
        size_t move_size = (array->size - index - 1) * array->element_size;
        memmove(dest, src, move_size);
    }

    array->size--;
    return MGEN_OK;
}

void* mgen_dyn_array_get(const mgen_dyn_array_t* array, size_t index) {
    if (!array) {
        mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
        return NULL;
    }

    if (index >= array->size) {
        mgen_handle_error(MGEN_ERROR_OUT_OF_BOUNDS, "Get index out of bounds");
        return NULL;
    }

    return (char*)array->data + (index * array->element_size);
}

mgen_error_t mgen_dyn_array_set(mgen_dyn_array_t* array, size_t index, const void* element) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (!element) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Element is NULL");
    }

    if (index >= array->size) {
        return mgen_handle_error(MGEN_ERROR_OUT_OF_BOUNDS, "Set index out of bounds");
    }

    void* dest = (char*)array->data + (index * array->element_size);
    memcpy(dest, element, array->element_size);

    return MGEN_OK;
}

size_t mgen_dyn_array_size(const mgen_dyn_array_t* array) {
    return array ? array->size : 0;
}

size_t mgen_dyn_array_capacity(const mgen_dyn_array_t* array) {
    return array ? array->capacity : 0;
}

void mgen_dyn_array_clear(mgen_dyn_array_t* array) {
    if (array) {
        array->size = 0;
    }
}

bool mgen_dyn_array_contains(const mgen_dyn_array_t* array, const void* element) {
    if (!array || !element) {
        return false;
    }

    for (size_t i = 0; i < array->size; i++) {
        void* item = (char*)array->data + (i * array->element_size);
        if (memcmp(item, element, array->element_size) == 0) {
            return true;
        }
    }

    return false;
}

mgen_error_t mgen_dyn_array_shrink_to_fit(mgen_dyn_array_t* array) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (array->size == 0) {
        // Keep at least minimal capacity
        return MGEN_OK;
    }

    if (array->size == array->capacity) {
        return MGEN_OK; // Already fitted
    }

    void* new_data = realloc(array->data, array->element_size * array->size);
    if (!new_data) {
        return mgen_handle_error(MGEN_ERROR_MEMORY, "Failed to shrink array");
    }

    array->data = new_data;
    array->capacity = array->size;
    return MGEN_OK;
}

void* mgen_dyn_array_back(const mgen_dyn_array_t* array) {
    if (!array || array->size == 0) {
        return NULL;
    }

    return (char*)array->data + ((array->size - 1) * array->element_size);
}

mgen_error_t mgen_dyn_array_pop_back(mgen_dyn_array_t* array) {
    if (!array) {
        return mgen_handle_error(MGEN_ERROR_NULL_PTR, "Array is NULL");
    }

    if (array->size == 0) {
        return mgen_handle_error(MGEN_ERROR_OUT_OF_BOUNDS, "Cannot pop from empty array");
    }

    array->size--;
    return MGEN_OK;
}

bool mgen_dyn_array_empty(const mgen_dyn_array_t* array) {
    return !array || array->size == 0;
}
