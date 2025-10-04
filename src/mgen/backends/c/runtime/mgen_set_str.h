/**
 * Simple hash set for strings
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_SET_STR_H
#define MGEN_SET_STR_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Hash set entry structure
typedef struct {
    char* value;       // String value (owned)
    size_t hash;
    bool occupied;
} set_str_entry;

// Hash set structure
typedef struct {
    set_str_entry* buckets;
    size_t size;           // Number of entries
    size_t capacity;       // Number of buckets
} set_str;

/**
 * Create a new string set
 * Supports {0} initialization with lazy bucket allocation
 */
set_str set_str_init(void);

/**
 * Insert a string into the set
 * Takes ownership of a copy of the string
 * Returns true if inserted (new), false if already present
 */
bool set_str_insert(set_str* set, const char* value);

/**
 * Check if string is in the set
 */
bool set_str_contains(const set_str* set, const char* value);

/**
 * Remove a string from the set
 * Returns true if removed, false if not found
 */
bool set_str_erase(set_str* set, const char* value);

/**
 * Get number of entries
 */
size_t set_str_size(const set_str* set);

/**
 * Check if set is empty
 */
bool set_str_empty(const set_str* set);

/**
 * Clear all entries (keep capacity)
 */
void set_str_clear(set_str* set);

/**
 * Free all memory
 */
void set_str_drop(set_str* set);

/**
 * Reserve capacity
 */
void set_str_reserve(set_str* set, size_t new_capacity);

#ifdef __cplusplus
}
#endif

#endif // MGEN_SET_STR_H
