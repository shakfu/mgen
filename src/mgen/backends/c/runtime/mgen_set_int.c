/**
 * Simple hash set for integers - Implementation
 * STC-compatible naming for drop-in replacement
 */

#include "mgen_set_int.h"
#include "mgen_error_handling.h"
#include <stdlib.h>

#define DEFAULT_BUCKET_COUNT 16

/**
 * Simple hash function for integers
 */
static size_t hash_int(int value, size_t bucket_count) {
    // For integers, we can use identity with modulo
    // Handle negative values by taking absolute value
    unsigned int u = (value < 0) ? (unsigned int)(-value) : (unsigned int)value;
    return u % bucket_count;
}

/**
 * Create a new entry
 */
static mgen_set_int_entry_t* set_int_entry_new(int value) {
    mgen_set_int_entry_t* entry = malloc(sizeof(mgen_set_int_entry_t));
    if (!entry) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate set entry");
        return NULL;
    }
    entry->value = value;
    entry->next = NULL;
    return entry;
}

/**
 * Free an entry chain
 */
static void set_int_entry_free(mgen_set_int_entry_t* entry) {
    while (entry) {
        mgen_set_int_entry_t* next = entry->next;
        free(entry);
        entry = next;
    }
}

set_int set_int_init(void) {
    set_int set;
    set.bucket_count = DEFAULT_BUCKET_COUNT;
    set.size = 0;
    set.buckets = calloc(DEFAULT_BUCKET_COUNT, sizeof(mgen_set_int_entry_t*));
    if (!set.buckets) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate set buckets");
        set.bucket_count = 0;
    }
    return set;
}

bool set_int_insert(set_int* set, int value) {
    if (!set) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL set");
        return false;
    }

    // Lazy initialization for {0}-initialized sets
    if (!set->buckets) {
        set->bucket_count = DEFAULT_BUCKET_COUNT;
        set->buckets = calloc(DEFAULT_BUCKET_COUNT, sizeof(mgen_set_int_entry_t*));
        if (!set->buckets) {
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate set buckets");
            set->bucket_count = 0;
            return false;
        }
    }

    size_t index = hash_int(value, set->bucket_count);

    // Check if value already exists
    mgen_set_int_entry_t* entry = set->buckets[index];
    while (entry) {
        if (entry->value == value) {
            return false; // Already present
        }
        entry = entry->next;
    }

    // Insert new entry at head of chain
    mgen_set_int_entry_t* new_entry = set_int_entry_new(value);
    if (!new_entry) {
        return false;
    }

    new_entry->next = set->buckets[index];
    set->buckets[index] = new_entry;
    set->size++;

    return true; // Inserted
}

bool set_int_contains(const set_int* set, int value) {
    if (!set || !set->buckets) {
        return false;
    }

    size_t index = hash_int(value, set->bucket_count);

    mgen_set_int_entry_t* entry = set->buckets[index];
    while (entry) {
        if (entry->value == value) {
            return true;
        }
        entry = entry->next;
    }

    return false;
}

bool set_int_remove(set_int* set, int value) {
    if (!set || !set->buckets) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "NULL or uninitialized set");
        return false;
    }

    size_t index = hash_int(value, set->bucket_count);

    mgen_set_int_entry_t** entry_ptr = &set->buckets[index];
    while (*entry_ptr) {
        mgen_set_int_entry_t* entry = *entry_ptr;
        if (entry->value == value) {
            *entry_ptr = entry->next;
            free(entry);
            set->size--;
            return true;
        }
        entry_ptr = &entry->next;
    }

    return false; // Not found
}

size_t set_int_size(const set_int* set) {
    return set ? set->size : 0;
}

bool set_int_empty(const set_int* set) {
    return !set || set->size == 0;
}

void set_int_clear(set_int* set) {
    if (!set || !set->buckets) {
        return;
    }

    for (size_t i = 0; i < set->bucket_count; i++) {
        if (set->buckets[i]) {
            set_int_entry_free(set->buckets[i]);
            set->buckets[i] = NULL;
        }
    }

    set->size = 0;
}

void set_int_drop(set_int* set) {
    if (!set) {
        return;
    }

    set_int_clear(set);
    free(set->buckets);
    set->buckets = NULL;
    set->bucket_count = 0;
    set->size = 0;
}

set_int_iter set_int_begin(const set_int* set) {
    set_int_iter iter;
    iter.set = set;
    iter.bucket_index = 0;
    iter.current_entry = NULL;
    iter.ref = NULL;

    if (!set || !set->buckets || set->size == 0) {
        return iter;
    }

    // Find first non-empty bucket
    for (size_t i = 0; i < set->bucket_count; i++) {
        if (set->buckets[i]) {
            iter.bucket_index = i;
            iter.current_entry = set->buckets[i];
            iter.ref = &iter.current_entry->value;
            break;
        }
    }

    return iter;
}

void set_int_next(set_int_iter* iter) {
    if (!iter || !iter->set || !iter->current_entry) {
        if (iter) {
            iter->ref = NULL;
        }
        return;
    }

    // Try next entry in current bucket chain
    if (iter->current_entry->next) {
        iter->current_entry = iter->current_entry->next;
        iter->ref = &iter->current_entry->value;
        return;
    }

    // Find next non-empty bucket
    for (size_t i = iter->bucket_index + 1; i < iter->set->bucket_count; i++) {
        if (iter->set->buckets[i]) {
            iter->bucket_index = i;
            iter->current_entry = iter->set->buckets[i];
            iter->ref = &iter->current_entry->value;
            return;
        }
    }

    // No more elements
    iter->current_entry = NULL;
    iter->ref = NULL;
}
