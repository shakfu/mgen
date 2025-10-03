/**
 * Simple hash set for integers
 * Clean, type-safe implementation for code generation
 */

#ifndef MGEN_SET_INT_H
#define MGEN_SET_INT_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Hash set entry for separate chaining
typedef struct mgen_set_int_entry {
    int value;
    struct mgen_set_int_entry* next;
} mgen_set_int_entry_t;

// Hash set structure (STC-compatible naming)
typedef struct {
    mgen_set_int_entry_t** buckets;
    size_t bucket_count;
    size_t size;
} set_int;

/**
 * Create a new integer set
 * Initial capacity defaults to 16 buckets
 */
set_int set_int_init(void);

/**
 * Insert an element into the set
 * Returns true if inserted (new), false if already present
 */
bool set_int_insert(set_int* set, int value);

/**
 * Check if element is in the set
 */
bool set_int_contains(const set_int* set, int value);

/**
 * Remove an element from the set
 * Returns true if removed, false if not found
 */
bool set_int_remove(set_int* set, int value);

/**
 * Get number of elements in set
 */
size_t set_int_size(const set_int* set);

/**
 * Check if set is empty
 */
bool set_int_empty(const set_int* set);

/**
 * Clear all elements (keep buckets allocated)
 */
void set_int_clear(set_int* set);

/**
 * Free all memory (STC-compatible drop function)
 */
void set_int_drop(set_int* set);

// Iterator support for set traversal
typedef struct {
    const set_int* set;
    size_t bucket_index;
    mgen_set_int_entry_t* current_entry;
    int* ref;  // Pointer to current value (STC-compatible)
} set_int_iter;

/**
 * Get iterator to beginning of set
 */
set_int_iter set_int_begin(const set_int* set);

/**
 * Advance iterator to next element
 */
void set_int_next(set_int_iter* iter);

#ifdef __cplusplus
}
#endif

#endif // MGEN_SET_INT_H
