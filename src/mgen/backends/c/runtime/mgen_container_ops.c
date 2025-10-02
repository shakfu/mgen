/**
 * MGen Runtime Library - STC Container Helper Operations Implementation
 */

#include "mgen_container_ops.h"
#include "mgen_string_ops.h"

// Container registry for automatic cleanup
typedef struct container_entry {
    void* container;
    void (*cleanup_func)(void*);
    char* name;
    struct container_entry* next;
} container_entry_t;

struct mgen_container_registry {
    container_entry_t* head;
    size_t count;
};

// String container helpers
struct cstr* mgen_cstr_from(const char* str) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

    // This would be implemented with actual STC cstr when available
    // For now, return NULL to indicate STC integration needed
    MGEN_SET_ERROR(MGEN_ERROR_RUNTIME, "STC cstr integration not yet available");
    return NULL;
}

const char* mgen_cstr_to_cstring(struct cstr* cstr) {
    if (!cstr) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "cstr is NULL");
        return NULL;
    }

    // This would be implemented with actual STC cstr when available
    MGEN_SET_ERROR(MGEN_ERROR_RUNTIME, "STC cstr integration not yet available");
    return NULL;
}

void mgen_cstr_free(struct cstr* cstr) {
    if (!cstr) return;

    // This would be implemented with actual STC cstr when available
    // For now, no-op
}

// Vector container helpers
int mgen_vec_bounds_check(size_t index, size_t size, const char* container_name) {
    if (index >= size) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_INDEX,
                           "%s index %zu out of range [0, %zu)",
                           container_name ? container_name : "vector",
                           index, size);
        return 0;
    }
    return 1;
}

void mgen_vec_index_error(size_t index, size_t size, const char* container_name) {
    MGEN_SET_ERROR_FMT(MGEN_ERROR_INDEX,
                       "%s index %zu out of range [0, %zu)",
                       container_name ? container_name : "vector",
                       index, size);
}

void* mgen_vec_at_safe(void* vec_ptr, size_t index, size_t element_size,
                       size_t (*size_func)(void*), const char* container_name) {
    if (!vec_ptr || !size_func) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid vector or size function");
        return NULL;
    }

    size_t size = size_func(vec_ptr);
    if (!mgen_vec_bounds_check(index, size, container_name)) {
        return NULL;
    }

    // This would use actual STC vector access when available
    // For now, return NULL to indicate bounds were checked
    return NULL;
}

// HashMap container helpers
int mgen_hmap_contains_key(void* hmap_ptr, const void* key,
                          int (*contains_func)(void*, const void*)) {
    if (!hmap_ptr || !key || !contains_func) {
        return 0;
    }

    return contains_func(hmap_ptr, key);
}

void* mgen_hmap_get_safe(void* hmap_ptr, const void* key,
                        void* (*get_func)(void*, const void*),
                        const char* key_str) {
    if (!hmap_ptr || !key || !get_func) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid hashmap or get function");
        return NULL;
    }

    void* result = get_func(hmap_ptr, key);
    if (!result) {
        MGEN_SET_ERROR_FMT(MGEN_ERROR_KEY, "Key '%s' not found in hashmap",
                           key_str ? key_str : "<unknown>");
        return NULL;
    }

    return result;
}

// HashSet container helpers
int mgen_hset_contains(void* hset_ptr, const void* element,
                      int (*contains_func)(void*, const void*)) {
    if (!hset_ptr || !element || !contains_func) {
        return 0;
    }

    return contains_func(hset_ptr, element);
}

// Container iteration helpers
void mgen_vec_enumerate(void* vec_ptr, size_t element_size,
                       size_t (*size_func)(void*),
                       void* (*at_func)(void*, size_t),
                       mgen_enumerate_callback_t callback,
                       void* userdata) {
    if (!vec_ptr || !size_func || !at_func || !callback) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid parameters for vector enumeration");
        return;
    }

    size_t size = size_func(vec_ptr);
    for (size_t i = 0; i < size; i++) {
        void* element = at_func(vec_ptr, i);
        if (element) {
            callback(i, element, userdata);
        }
    }
}

void mgen_hmap_items(void* hmap_ptr,
                    void (*iter_func)(void*, mgen_items_callback_t, void*),
                    mgen_items_callback_t callback,
                    void* userdata) {
    if (!hmap_ptr || !iter_func || !callback) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid parameters for hashmap iteration");
        return;
    }

    iter_func(hmap_ptr, callback, userdata);
}

// Container comparison helpers
int mgen_vec_equal(void* vec1, void* vec2,
                  size_t (*size_func)(void*),
                  void* (*at_func)(void*, size_t),
                  int (*element_equal)(const void*, const void*)) {
    if (!vec1 || !vec2 || !size_func || !at_func || !element_equal) {
        return 0;
    }

    size_t size1 = size_func(vec1);
    size_t size2 = size_func(vec2);

    if (size1 != size2) {
        return 0;
    }

    for (size_t i = 0; i < size1; i++) {
        void* elem1 = at_func(vec1, i);
        void* elem2 = at_func(vec2, i);
        if (!element_equal(elem1, elem2)) {
            return 0;
        }
    }

    return 1;
}

int mgen_hmap_equal(void* hmap1, void* hmap2,
                   size_t (*size_func)(void*),
                   int (*equal_func)(void*, void*)) {
    if (!hmap1 || !hmap2 || !size_func || !equal_func) {
        return 0;
    }

    size_t size1 = size_func(hmap1);
    size_t size2 = size_func(hmap2);

    if (size1 != size2) {
        return 0;
    }

    return equal_func(hmap1, hmap2);
}

// Container conversion helpers
struct vec_cstr* mgen_string_array_to_vec_cstr(mgen_string_array_t* str_array) {
    if (!str_array) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String array is NULL");
        return NULL;
    }

    // This would be implemented with actual STC vec_cstr when available
    MGEN_SET_ERROR(MGEN_ERROR_RUNTIME, "STC vec_cstr integration not yet available");
    return NULL;
}

mgen_string_array_t* mgen_vec_cstr_to_string_array(struct vec_cstr* vec) {
    if (!vec) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Vector is NULL");
        return NULL;
    }

    // This would be implemented with actual STC vec_cstr when available
    MGEN_SET_ERROR(MGEN_ERROR_RUNTIME, "STC vec_cstr integration not yet available");
    return NULL;
}

// Container memory management helpers
mgen_container_registry_t* mgen_container_registry_new(void) {
    mgen_container_registry_t* registry = malloc(sizeof(mgen_container_registry_t));
    if (!registry) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate container registry");
        return NULL;
    }

    registry->head = NULL;
    registry->count = 0;
    return registry;
}

void mgen_container_registry_free(mgen_container_registry_t* registry) {
    if (!registry) return;

    mgen_cleanup_containers(registry);
    free(registry);
}

mgen_error_t mgen_register_container(mgen_container_registry_t* registry,
                                    void* container,
                                    void (*cleanup_func)(void*),
                                    const char* name) {
    if (!registry || !container || !cleanup_func) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid parameters for container registration");
        return MGEN_ERROR_VALUE;
    }

    container_entry_t* entry = malloc(sizeof(container_entry_t));
    if (!entry) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate container entry");
        return MGEN_ERROR_MEMORY;
    }

    entry->container = container;
    entry->cleanup_func = cleanup_func;
    entry->name = name ? mgen_strdup(name) : NULL;
    entry->next = registry->head;

    registry->head = entry;
    registry->count++;

    return MGEN_OK;
}

void mgen_cleanup_containers(mgen_container_registry_t* registry) {
    if (!registry) return;

    container_entry_t* current = registry->head;
    while (current) {
        container_entry_t* next = current->next;

        if (current->cleanup_func && current->container) {
            current->cleanup_func(current->container);
        }
        free(current->name);
        free(current);

        current = next;
    }

    registry->head = NULL;
    registry->count = 0;
}

// Python-style container operations
size_t mgen_len(void* container, size_t (*size_func)(void*)) {
    if (!container || !size_func) {
        return 0;
    }
    return size_func(container);
}

int mgen_bool_container(void* container, size_t (*size_func)(void*)) {
    return mgen_len(container, size_func) > 0;
}

int mgen_in_vec(void* vec_ptr, const void* element,
               size_t (*size_func)(void*),
               void* (*at_func)(void*, size_t),
               int (*element_equal)(const void*, const void*)) {
    if (!vec_ptr || !element || !size_func || !at_func || !element_equal) {
        return 0;
    }

    size_t size = size_func(vec_ptr);
    for (size_t i = 0; i < size; i++) {
        void* vec_element = at_func(vec_ptr, i);
        if (vec_element && element_equal(element, vec_element)) {
            return 1;
        }
    }

    return 0;
}

int mgen_in_hmap(void* hmap_ptr, const void* key,
                int (*contains_func)(void*, const void*)) {
    return mgen_hmap_contains_key(hmap_ptr, key, contains_func);
}

// Python-style string formatting for containers
char* mgen_vec_repr(void* vec_ptr,
                   size_t (*size_func)(void*),
                   void* (*at_func)(void*, size_t),
                   char* (*element_repr)(const void*)) {
    if (!vec_ptr || !size_func || !at_func || !element_repr) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid parameters for vector representation");
        return NULL;
    }

    size_t size = size_func(vec_ptr);
    if (size == 0) {
        return mgen_strdup("[]");
    }

    // Build representation string
    mgen_string_array_t* parts = mgen_string_array_new();
    if (!parts) return NULL;

    for (size_t i = 0; i < size; i++) {
        void* element = at_func(vec_ptr, i);
        if (element) {
            char* elem_repr = element_repr(element);
            if (elem_repr) {
                if (mgen_string_array_add(parts, elem_repr) != MGEN_OK) {
                    free(elem_repr);
                    mgen_string_array_free(parts);
                    return NULL;
                }
            }
        }
    }

    char* joined = mgen_join(", ", parts);
    mgen_string_array_free(parts);

    if (!joined) return NULL;

    // Add brackets
    char* result = malloc(strlen(joined) + 3); // "[]" + null terminator
    if (!result) {
        free(joined);
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for vector representation");
        return NULL;
    }

    sprintf(result, "[%s]", joined);
    free(joined);

    return result;
}

char* mgen_hmap_repr(void* hmap_ptr, char* (*repr_func)(void*)) {
    if (!hmap_ptr || !repr_func) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid parameters for hashmap representation");
        return NULL;
    }

    // This would be implemented with actual STC hashmap iteration when available
    return mgen_strdup("{}"); // Simplified representation
}
