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

/**
 * Create a map with specific initial capacity
 */

/**
 * Insert or update a key-value pair
 * Key is copied (strdup), so caller retains ownership of input string
 * Returns true if inserted, false if updated existing key
 */

/**
 * Get value for a key
 * Returns pointer to value if found, NULL if not found
 */

/**
 * Check if key exists in map
 */

/**
 * Remove a key-value pair
 * Returns true if removed, false if key didn't exist
 */

/**
 * Get number of entries in map
 */

/**
 * Free all memory associated with map
 * Frees all keys and the map structure itself
 */

/**
 * Clear all entries but keep the map structure
 */

/**
 * Simple hash table for string -> int mappings
 * Implementation using separate chaining for collision resolution
 */

#include "mgen_error_handling.h"
#include <stdlib.h>
#include <string.h>

#define DEFAULT_BUCKET_COUNT 16
#define LOAD_FACTOR_THRESHOLD 0.75

/**
 * djb2 hash function - simple and effective for strings
 */
static unsigned long hash_string(const char* str) {
    unsigned long hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    return hash;
}

/**
 * Create a new entry
 */
static mgen_str_int_entry_t* entry_new(const char* key, int value) {
    mgen_str_int_entry_t* entry = malloc(sizeof(mgen_str_int_entry_t));
    if (!entry) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate map entry");
        return NULL;
    }

    entry->key = strdup(key);
    if (!entry->key) {
        free(entry);
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to duplicate key");
        return NULL;
    }

    entry->value = value;
    entry->next = NULL;
    return entry;
}

/**
 * Free an entry and its chain
 */
static void entry_free(mgen_str_int_entry_t* entry) {
    while (entry) {
        mgen_str_int_entry_t* next = entry->next;
        free(entry->key);
        free(entry);
        entry = next;
    }
}

static mgen_str_int_map_t* mgen_str_int_map_new_with_capacity(size_t capacity) {
    mgen_str_int_map_t* map = malloc(sizeof(mgen_str_int_map_t));
    if (!map) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate map");
        return NULL;
    }

    map->buckets = calloc(capacity, sizeof(mgen_str_int_entry_t*));
    if (!map->buckets) {
        free(map);
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate buckets");
        return NULL;
    }

    map->bucket_count = capacity;
    map->size = 0;
    return map;
}

static mgen_str_int_map_t* mgen_str_int_map_new(void) {
    return mgen_str_int_map_new_with_capacity(DEFAULT_BUCKET_COUNT);
}

static bool mgen_str_int_map_insert(mgen_str_int_map_t* map, const char* key, int value) {
    if (!map || !key) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL map or key");
        return false;
    }

    unsigned long hash = hash_string(key);
    size_t index = hash % map->bucket_count;

    // Check if key already exists
    mgen_str_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            // Update existing value
            entry->value = value;
            return false; // Updated, not inserted
        }
        entry = entry->next;
    }

    // Insert new entry at head of chain
    mgen_str_int_entry_t* new_entry = entry_new(key, value);
    if (!new_entry) {
        return false;
    }

    new_entry->next = map->buckets[index];
    map->buckets[index] = new_entry;
    map->size++;

    return true; // Inserted
}

static int* mgen_str_int_map_get(mgen_str_int_map_t* map, const char* key) {
    if (!map || !key) {
        return NULL;
    }

    unsigned long hash = hash_string(key);
    size_t index = hash % map->bucket_count;

    mgen_str_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            return &entry->value;
        }
        entry = entry->next;
    }

    return NULL;
}

static bool mgen_str_int_map_contains(mgen_str_int_map_t* map, const char* key) {
    return mgen_str_int_map_get(map, key) != NULL;
}

static bool mgen_str_int_map_remove(mgen_str_int_map_t* map, const char* key) {
    if (!map || !key) {
        return false;
    }

    unsigned long hash = hash_string(key);
    size_t index = hash % map->bucket_count;

    mgen_str_int_entry_t** entry_ptr = &map->buckets[index];
    while (*entry_ptr) {
        mgen_str_int_entry_t* entry = *entry_ptr;
        if (strcmp(entry->key, key) == 0) {
            *entry_ptr = entry->next;
            free(entry->key);
            free(entry);
            map->size--;
            return true;
        }
        entry_ptr = &entry->next;
    }

    return false;
}

static inline size_t mgen_str_int_map_size(const mgen_str_int_map_t* map) {
    return map ? map->size : 0;
}

static inline void mgen_str_int_map_clear(mgen_str_int_map_t* map) {
    if (!map) {
        return;
    }

    for (size_t i = 0; i < map->bucket_count; i++) {
        if (map->buckets[i]) {
            entry_free(map->buckets[i]);
            map->buckets[i] = NULL;
        }
    }

    map->size = 0;
}

static void mgen_str_int_map_free(mgen_str_int_map_t* map) {
    if (!map) {
        return;
    }

    mgen_str_int_map_clear(map);
    free(map->buckets);
    free(map);
}


// Implementation

#ifdef __cplusplus
}
#endif

#endif // MGEN_STR_INT_MAP_H
