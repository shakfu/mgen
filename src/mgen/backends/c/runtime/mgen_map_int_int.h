/**
 * Simple hash map for int → int mappings
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_MAP_INT_INT_H
#define MGEN_MAP_INT_INT_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Hash map entry for separate chaining
typedef struct mgen_map_int_int_entry {
    int key;
    int value;
    struct mgen_map_int_int_entry* next;
} mgen_map_int_int_entry_t;

// Hash map structure (STC-compatible naming)
typedef struct {
    mgen_map_int_int_entry_t** buckets;
    size_t bucket_count;
    size_t size;
} map_int_int;

/**
 * Create a new int→int map
 * Initial capacity defaults to 16 buckets
 */
map_int_int map_int_int_init(void);

/**
 * Insert or update a key-value pair
 * Returns true if inserted (new key), false if updated existing key
 */
bool map_int_int_insert(map_int_int* map, int key, int value);

/**
 * Get value for a key
 * Returns pointer to value if found, NULL if not found
 */
int* map_int_int_get(map_int_int* map, int key);

/**
 * Check if key exists in map
 */
bool map_int_int_contains(const map_int_int* map, int key);

/**
 * Remove a key-value pair
 * Returns true if removed, false if key didn't exist
 */
bool map_int_int_remove(map_int_int* map, int key);

/**
 * Get number of entries in map
 */
size_t map_int_int_size(const map_int_int* map);

/**
 * Check if map is empty
 */
bool map_int_int_empty(const map_int_int* map);

/**
 * Clear all entries (keep buckets allocated)
 */
void map_int_int_clear(map_int_int* map);

/**
 * Free all memory (STC-compatible drop function)
 */
void map_int_int_drop(map_int_int* map);

#ifdef __cplusplus
}
#endif

#endif // MGEN_MAP_INT_INT_H
