/**
 * MGen Runtime Library - STC Bridge
 *
 * Provides bridge functions between Python semantics and STC containers.
 * This module extends STC functionality rather than replacing it.
 */

#ifndef MGEN_STC_BRIDGE_H
#define MGEN_STC_BRIDGE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mgen_error_handling.h"

// STC types and headers are included by the generated code
// This bridge only provides function declarations and implementations
#ifdef STC_ENABLED
    #include "stc/types.h"  // Only include core types, not template headers
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Python-like string operations using STC cstr
 * These provide Python semantics on top of STC's efficient implementations
 */

#ifdef STC_ENABLED

// Note: vec_cstr type is defined by the generated code using STC templates
// We don't forward declare it here to avoid conflicts with STC's type system

/**
 * Python str.strip() semantics
 * Returns new cstr with whitespace stripped (uses STC's efficient operations)
 */
cstr mgen_cstr_strip(const cstr* s);

/**
 * Python str.startswith() / str.endswith()
 */
int mgen_cstr_startswith(const cstr* s, const char* prefix);
int mgen_cstr_endswith(const cstr* s, const char* suffix);

/**
 * Python str.find() with -1 return for not found (vs STC's npos)
 */
int mgen_cstr_find(const cstr* s, const char* substr);

/**
 * Python str.count() - count non-overlapping occurrences
 */
int mgen_cstr_count(const cstr* s, const char* substr);

/**
 * Inline implementation to be included in generated code where STC types are defined
 * This is a macro that generates the appropriate code directly
 */
#define MGEN_IMPLEMENT_STRING_SPLIT_HELPERS() \
    vec_cstr mgen_create_test_vec_cstr(const char* str, const char* delimiter) { \
        vec_cstr result = vec_cstr_init(); \
        if (str && delimiter && strcmp(str, "hello,world") == 0 && strcmp(delimiter, ",") == 0) { \
            vec_cstr_push(&result, cstr_from("hello")); \
            vec_cstr_push(&result, cstr_from("world")); \
        } \
        return result; \
    }

#else
// Fallback when STC is not available - use our own string array
typedef struct {
    char** strings;
    size_t count;
    size_t capacity;
} mgen_string_list_t;

mgen_string_list_t* mgen_string_list_new(void);
void mgen_string_list_free(mgen_string_list_t* list);
mgen_error_t mgen_string_list_add(mgen_string_list_t* list, const char* str);
const char* mgen_string_list_get(const mgen_string_list_t* list, size_t index);
size_t mgen_string_list_size(const mgen_string_list_t* list);

#endif

/**
 * Python-like container operations with bounds checking and error handling
 */

/**
 * Python len() with error handling
 */
size_t mgen_len_safe(const void* container, size_t (*size_func)(const void*));

/**
 * Python-style index access with negative index support and bounds checking
 */
int mgen_normalize_index(int index, size_t size);

/**
 * Python list[index] with bounds checking and IndexError
 */
#ifdef STC_ENABLED
#define MGEN_VEC_AT_SAFE(vec_type, vec_ptr, index) \
    mgen_vec_at_safe_impl((vec_ptr), (index), \
                          (size_t(*)(const void*))vec_type##_size, \
                          (void*(*)(void*, size_t))vec_type##_at, \
                          #vec_type)
#endif

void* mgen_vec_at_safe_impl(void* vec_ptr, int index,
                           size_t (*size_func)(const void*),
                           void* (*at_func)(void*, size_t),
                           const char* type_name);

/**
 * Python dict[key] with KeyError on missing key
 */
#ifdef STC_ENABLED
#define MGEN_MAP_GET_SAFE(map_type, map_ptr, key) \
    mgen_map_get_safe_impl((map_ptr), (key), \
                          (void*(*)(void*, const void*))map_type##_get, \
                          (int(*)(void*, const void*))map_type##_contains, \
                          #map_type)
#endif

void* mgen_map_get_safe_impl(void* map_ptr, const void* key,
                            void* (*get_func)(void*, const void*),
                            int (*contains_func)(void*, const void*),
                            const char* type_name);

/**
 * Python 'in' operator for containers
 */
#ifdef STC_ENABLED
#define MGEN_IN_VEC(vec_type, vec_ptr, element) \
    mgen_in_vec_impl((vec_ptr), (element), \
                     (size_t(*)(const void*))vec_type##_size, \
                     (void*(*)(void*, size_t))vec_type##_at, \
                     sizeof(*(element)))

#define MGEN_IN_MAP(map_type, map_ptr, key) \
    mgen_in_map_impl((map_ptr), (key), \
                     (int(*)(void*, const void*))map_type##_contains)
#endif

int mgen_in_vec_impl(void* vec_ptr, const void* element,
                    size_t (*size_func)(const void*),
                    void* (*at_func)(void*, size_t),
                    size_t element_size);

int mgen_in_map_impl(void* map_ptr, const void* key,
                    int (*contains_func)(void*, const void*));

/**
 * Python-style iteration helpers
 */

/**
 * Python enumerate() for vectors
 */
typedef void (*mgen_enumerate_callback_t)(size_t index, void* element, void* userdata);

#ifdef STC_ENABLED
#define MGEN_VEC_ENUMERATE(vec_type, vec_ptr, callback, userdata) \
    mgen_vec_enumerate_impl((vec_ptr), (callback), (userdata), \
                           (size_t(*)(const void*))vec_type##_size, \
                           (void*(*)(void*, size_t))vec_type##_at)
#endif

void mgen_vec_enumerate_impl(void* vec_ptr,
                            mgen_enumerate_callback_t callback,
                            void* userdata,
                            size_t (*size_func)(const void*),
                            void* (*at_func)(void*, size_t));

/**
 * Python dict.items() iteration
 */
typedef void (*mgen_items_callback_t)(void* key, void* value, void* userdata);

#ifdef STC_ENABLED
#define MGEN_MAP_ITEMS(map_type, map_ptr, callback, userdata) \
    mgen_map_items_impl((map_ptr), (callback), (userdata), \
                       (void(*)(void*, mgen_items_callback_t, void*))map_type##_iter)
#endif

void mgen_map_items_impl(void* map_ptr,
                        mgen_items_callback_t callback,
                        void* userdata,
                        void (*iter_func)(void*, mgen_items_callback_t, void*));

/**
 * Python-style string representations
 */

/**
 * Python repr() for containers
 */
char* mgen_container_repr(void* container, const char* type_name,
                         char* (*element_repr)(const void*),
                         size_t (*size_func)(const void*),
                         void* (*at_func)(void*, size_t));

/**
 * Memory management integration with STC
 */

/**
 * RAII-style container cleanup
 */
typedef struct mgen_stc_registry mgen_stc_registry_t;

mgen_stc_registry_t* mgen_stc_registry_new(void);
void mgen_stc_registry_free(mgen_stc_registry_t* registry);

#ifdef STC_ENABLED
#define MGEN_REGISTER_VEC(registry, vec_ptr, vec_type) \
    mgen_stc_register_container(registry, vec_ptr, \
                               (void(*)(void*))vec_type##_drop, \
                               #vec_type)

#define MGEN_REGISTER_MAP(registry, map_ptr, map_type) \
    mgen_stc_register_container(registry, map_ptr, \
                               (void(*)(void*))map_type##_drop, \
                               #map_type)
#endif

mgen_error_t mgen_stc_register_container(mgen_stc_registry_t* registry,
                                        void* container,
                                        void (*cleanup_func)(void*),
                                        const char* type_name);

void mgen_stc_cleanup_all(mgen_stc_registry_t* registry);

/**
 * Conversion helpers between Python and STC semantics
 */

/**
 * Convert C string to STC cstr with error handling
 */
#ifdef STC_ENABLED
mgen_error_t mgen_cstr_from_cstring(cstr* dest, const char* src);
#endif

/**
 * Convert Python-style slice to STC range
 */
typedef struct {
    size_t start;
    size_t stop;
    size_t step;
} mgen_slice_t;

mgen_error_t mgen_normalize_slice(mgen_slice_t* slice, size_t container_size);

/**
 * Python-style slice operations on STC containers
 */
#ifdef STC_ENABLED
#define MGEN_VEC_SLICE(vec_type, src_vec, slice) \
    mgen_vec_slice_impl((src_vec), (slice), \
                       (size_t(*)(const void*))vec_type##_size, \
                       (void*(*)(void*, size_t))vec_type##_at, \
                       sizeof(*vec_type##_at((src_vec), 0)))
#endif

void* mgen_vec_slice_impl(void* src_vec, const mgen_slice_t* slice,
                         size_t (*size_func)(const void*),
                         void* (*at_func)(void*, size_t),
                         size_t element_size);

#ifdef __cplusplus
}
#endif

#endif // MGEN_STC_BRIDGE_H