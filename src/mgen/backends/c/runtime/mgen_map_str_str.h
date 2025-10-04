/**
 * Simple hash map for string→string mappings
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_MAP_STR_STR_H
#define MGEN_MAP_STR_STR_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Hash map entry structure
typedef struct {
    char* key;
    char* value;
    size_t hash;
    bool occupied;
} map_str_str_entry;

// Hash map structure
typedef struct {
    map_str_str_entry* buckets;
    size_t size;           // Number of entries
    size_t capacity;       // Number of buckets
} map_str_str;

/**
 * Create a new string→string map
 * Supports {0} initialization with lazy bucket allocation
 */
map_str_str map_str_str_init(void);

/**
 * Insert or update a key-value pair
 * Takes ownership of copies of both key and value
 */
void map_str_str_insert(map_str_str* map, const char* key, const char* value);

/**
 * Get value for a key (returns pointer to value or NULL if not found)
 */
char** map_str_str_get(map_str_str* map, const char* key);

/**
 * Check if key exists in map
 */
bool map_str_str_contains(map_str_str* map, const char* key);

/**
 * Get number of entries
 */
size_t map_str_str_size(const map_str_str* map);

/**
 * Remove a key-value pair
 */
void map_str_str_erase(map_str_str* map, const char* key);

/**
 * Clear all entries (keep capacity)
 */
void map_str_str_clear(map_str_str* map);

/**
 * Free all memory
 */
void map_str_str_drop(map_str_str* map);

/**
 * Check if map is empty
 */
bool map_str_str_empty(const map_str_str* map);

/**
 * Reserve capacity
 */
void map_str_str_reserve(map_str_str* map, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_MAP_STR_STR_H
