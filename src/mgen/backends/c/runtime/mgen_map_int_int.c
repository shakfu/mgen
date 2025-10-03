/**
 * Simple hash map for int → int - Implementation
 * STC-compatible naming for drop-in replacement
 */

#include "mgen_map_int_int.h"
#include "mgen_error_handling.h"
#include <stdlib.h>

#define DEFAULT_BUCKET_COUNT 16

/**
 * Simple hash function for integers
 */
static size_t map_int_int_hash(int key, size_t bucket_count) {
    // For integers, use modulo with handling for negative values
    unsigned int u = (key < 0) ? (unsigned int)(-key) : (unsigned int)key;
    return u % bucket_count;
}

/**
 * Create a new entry
 */
static mgen_map_int_int_entry_t* map_int_int_entry_new(int key, int value) {
    mgen_map_int_int_entry_t* entry = malloc(sizeof(mgen_map_int_int_entry_t));
    if (!entry) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate map entry");
        return NULL;
    }
    entry->key = key;
    entry->value = value;
    entry->next = NULL;
    return entry;
}

/**
 * Free an entry chain
 */
static void map_int_int_entry_free(mgen_map_int_int_entry_t* entry) {
    while (entry) {
        mgen_map_int_int_entry_t* next = entry->next;
        free(entry);
        entry = next;
    }
}

map_int_int map_int_int_init(void) {
    map_int_int map;
    map.bucket_count = DEFAULT_BUCKET_COUNT;
    map.size = 0;
    map.buckets = calloc(DEFAULT_BUCKET_COUNT, sizeof(mgen_map_int_int_entry_t*));
    if (!map.buckets) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate map buckets");
        map.bucket_count = 0;
    }
    return map;
}

bool map_int_int_insert(map_int_int* map, int key, int value) {
    if (!map) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL map");
        return false;
    }

    // Lazy initialization for {0}-initialized maps
    if (!map->buckets) {
        map->bucket_count = DEFAULT_BUCKET_COUNT;
        map->buckets = calloc(DEFAULT_BUCKET_COUNT, sizeof(mgen_map_int_int_entry_t*));
        if (!map->buckets) {
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate map buckets");
            map->bucket_count = 0;
            return false;
        }
    }

    size_t index = map_int_int_hash(key, map->bucket_count);

    // Check if key already exists
    mgen_map_int_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (entry->key == key) {
            // Update existing value
            entry->value = value;
            return false; // Updated, not inserted
        }
        entry = entry->next;
    }

    // Insert new entry at head of chain
    mgen_map_int_int_entry_t* new_entry = map_int_int_entry_new(key, value);
    if (!new_entry) {
        return false;
    }

    new_entry->next = map->buckets[index];
    map->buckets[index] = new_entry;
    map->size++;

    return true; // Inserted
}

int* map_int_int_get(map_int_int* map, int key) {
    if (!map || !map->buckets) {
        return NULL;
    }

    size_t index = map_int_int_hash(key, map->bucket_count);

    mgen_map_int_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (entry->key == key) {
            return &entry->value;
        }
        entry = entry->next;
    }

    return NULL;
}

bool map_int_int_contains(const map_int_int* map, int key) {
    if (!map || !map->buckets) {
        return false;
    }

    size_t index = map_int_int_hash(key, map->bucket_count);

    mgen_map_int_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (entry->key == key) {
            return true;
        }
        entry = entry->next;
    }

    return false;
}

bool map_int_int_remove(map_int_int* map, int key) {
    if (!map || !map->buckets) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL or uninitialized map");
        return false;
    }

    size_t index = map_int_int_hash(key, map->bucket_count);

    mgen_map_int_int_entry_t** entry_ptr = &map->buckets[index];
    while (*entry_ptr) {
        mgen_map_int_int_entry_t* entry = *entry_ptr;
        if (entry->key == key) {
            *entry_ptr = entry->next;
            free(entry);
            map->size--;
            return true;
        }
        entry_ptr = &entry->next;
    }

    return false; // Not found
}

size_t map_int_int_size(const map_int_int* map) {
    return map ? map->size : 0;
}

bool map_int_int_empty(const map_int_int* map) {
    return !map || map->size == 0;
}

void map_int_int_clear(map_int_int* map) {
    if (!map || !map->buckets) {
        return;
    }

    for (size_t i = 0; i < map->bucket_count; i++) {
        if (map->buckets[i]) {
            map_int_int_entry_free(map->buckets[i]);
            map->buckets[i] = NULL;
        }
    }

    map->size = 0;
}

void map_int_int_drop(map_int_int* map) {
    if (!map) {
        return;
    }

    map_int_int_clear(map);
    free(map->buckets);
    map->buckets = NULL;
    map->bucket_count = 0;
    map->size = 0;
}
