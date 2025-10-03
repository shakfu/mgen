/**
 * Simple hash table for string -> int mappings
 * Owns string keys (uses strdup/free)
 * Clean, understandable implementation without macro magic
 */

#ifndef MGEN_STR_INT_MAP_H
#define MGEN_STR_INT_MAP_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Hash table entry
typedef struct mgen_str_int_entry {
    char* key;                          // Owned string (strdup'd)
    int value;
    struct mgen_str_int_entry* next;    // For collision chaining
} mgen_str_int_entry_t;

// Hash table structure
typedef struct {
    mgen_str_int_entry_t** buckets;
    size_t bucket_count;
    size_t size;                        // Number of entries
} mgen_str_int_map_t;

/**
 * Create a new string-to-int map
 * Initial capacity defaults to 16 buckets
 */
mgen_str_int_map_t* mgen_str_int_map_new(void);

/**
 * Create a map with specific initial capacity
 */
mgen_str_int_map_t* mgen_str_int_map_new_with_capacity(size_t capacity);

/**
 * Insert or update a key-value pair
 * Key is copied (strdup), so caller retains ownership of input string
 * Returns true if inserted, false if updated existing key
 */
bool mgen_str_int_map_insert(mgen_str_int_map_t* map, const char* key, int value);

/**
 * Get value for a key
 * Returns pointer to value if found, NULL if not found
 */
int* mgen_str_int_map_get(mgen_str_int_map_t* map, const char* key);

/**
 * Check if key exists in map
 */
bool mgen_str_int_map_contains(mgen_str_int_map_t* map, const char* key);

/**
 * Remove a key-value pair
 * Returns true if removed, false if key didn't exist
 */
bool mgen_str_int_map_remove(mgen_str_int_map_t* map, const char* key);

/**
 * Get number of entries in map
 */
size_t mgen_str_int_map_size(const mgen_str_int_map_t* map);

/**
 * Free all memory associated with map
 * Frees all keys and the map structure itself
 */
void mgen_str_int_map_free(mgen_str_int_map_t* map);

/**
 * Clear all entries but keep the map structure
 */
void mgen_str_int_map_clear(mgen_str_int_map_t* map);

#ifdef __cplusplus
}
#endif

#endif // MGEN_STR_INT_MAP_H
