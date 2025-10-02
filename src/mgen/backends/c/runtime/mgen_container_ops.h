/**
 * MGen Runtime Library - STC Container Helper Operations
 *
 * Provides helper functions for STC (Smart Template Containers) operations.
 * These functions bridge Python container semantics with STC implementations.
 */

#ifndef MGEN_CONTAINER_OPS_H
#define MGEN_CONTAINER_OPS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mgen_error_handling.h"
#include "mgen_string_ops.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations for STC containers
// These will be defined when STC headers are included
struct cstr;
struct vec_cstr;
struct hmap_cstr_int;
struct hset_cstr;

/**
 * String container helpers
 */

/**
 * Create a new STC cstr from C string
 */
struct cstr* mgen_cstr_from(const char* str);

/**
 * Get C string from STC cstr
 */
const char* mgen_cstr_to_cstring(struct cstr* cstr);

/**
 * Free STC cstr safely
 */
void mgen_cstr_free(struct cstr* cstr);

/**
 * Vector container helpers
 */

/**
 * Check if vector index is valid
 */
int mgen_vec_bounds_check(size_t index, size_t size, const char* container_name);

/**
 * Print vector bounds error
 */
void mgen_vec_index_error(size_t index, size_t size, const char* container_name);

/**
 * Safe vector access with bounds checking
 */
void* mgen_vec_at_safe(void* vec_ptr, size_t index, size_t element_size,
                       size_t (*size_func)(void*), const char* container_name);

/**
 * HashMap container helpers
 */

/**
 * Check if key exists in hashmap
 */
int mgen_hmap_contains_key(void* hmap_ptr, const void* key,
                          int (*contains_func)(void*, const void*));

/**
 * Safe hashmap get with KeyError on missing key
 */
void* mgen_hmap_get_safe(void* hmap_ptr, const void* key,
                        void* (*get_func)(void*, const void*),
                        const char* key_str);

/**
 * HashSet container helpers
 */

/**
 * Check if element exists in hashset
 */
int mgen_hset_contains(void* hset_ptr, const void* element,
                      int (*contains_func)(void*, const void*));

/**
 * Container iteration helpers
 */

/**
 * Python-style enumerate for vectors
 * Calls callback for each (index, element) pair
 */
typedef void (*mgen_enumerate_callback_t)(size_t index, void* element, void* userdata);

void mgen_vec_enumerate(void* vec_ptr, size_t element_size,
                       size_t (*size_func)(void*),
                       void* (*at_func)(void*, size_t),
                       mgen_enumerate_callback_t callback,
                       void* userdata);

/**
 * Python-style items() iteration for hashmaps
 * Calls callback for each (key, value) pair
 */
typedef void (*mgen_items_callback_t)(void* key, void* value, void* userdata);

void mgen_hmap_items(void* hmap_ptr,
                    void (*iter_func)(void*, mgen_items_callback_t, void*),
                    mgen_items_callback_t callback,
                    void* userdata);

/**
 * Container comparison helpers
 */

/**
 * Compare two vectors element by element
 */
int mgen_vec_equal(void* vec1, void* vec2,
                  size_t (*size_func)(void*),
                  void* (*at_func)(void*, size_t),
                  int (*element_equal)(const void*, const void*));

/**
 * Compare two hashmaps
 */
int mgen_hmap_equal(void* hmap1, void* hmap2,
                   size_t (*size_func)(void*),
                   int (*equal_func)(void*, void*));

/**
 * Container conversion helpers
 */

/**
 * Convert string array to STC vector of cstr
 */
struct vec_cstr* mgen_string_array_to_vec_cstr(mgen_string_array_t* str_array);

/**
 * Convert STC vector of cstr to string array
 */
mgen_string_array_t* mgen_vec_cstr_to_string_array(struct vec_cstr* vec);

/**
 * Container memory management helpers
 */

/**
 * Register container for automatic cleanup
 */
typedef struct mgen_container_registry mgen_container_registry_t;

mgen_container_registry_t* mgen_container_registry_new(void);
void mgen_container_registry_free(mgen_container_registry_t* registry);

mgen_error_t mgen_register_container(mgen_container_registry_t* registry,
                                    void* container,
                                    void (*cleanup_func)(void*),
                                    const char* name);

void mgen_cleanup_containers(mgen_container_registry_t* registry);

/**
 * Python-style container operations
 */

/**
 * Python len() for any container
 */
size_t mgen_len(void* container, size_t (*size_func)(void*));

/**
 * Python bool() for containers (True if not empty)
 */
int mgen_bool_container(void* container, size_t (*size_func)(void*));

/**
 * Python in operator for vectors
 */
int mgen_in_vec(void* vec_ptr, const void* element,
               size_t (*size_func)(void*),
               void* (*at_func)(void*, size_t),
               int (*element_equal)(const void*, const void*));

/**
 * Python in operator for hashmaps (check key)
 */
int mgen_in_hmap(void* hmap_ptr, const void* key,
                int (*contains_func)(void*, const void*));

/**
 * Python-style string formatting for containers
 */
char* mgen_vec_repr(void* vec_ptr,
                   size_t (*size_func)(void*),
                   void* (*at_func)(void*, size_t),
                   char* (*element_repr)(const void*));

char* mgen_hmap_repr(void* hmap_ptr,
                    char* (*repr_func)(void*));

#ifdef __cplusplus
}
#endif

#endif // MGEN_CONTAINER_OPS_H
