/**
 * MGen LLVM Backend - String Operations Runtime
 *
 * Minimal string operations for LLVM backend
 */

#ifndef MGEN_LLVM_STRING_H
#define MGEN_LLVM_STRING_H

#include <stddef.h>

// String array type (for split results)
typedef struct {
    char** strings;
    size_t count;
    size_t capacity;
} mgen_string_array_t;

/**
 * Create a new string array
 */
mgen_string_array_t* mgen_string_array_new(void);

/**
 * Free a string array
 */
void mgen_string_array_free(mgen_string_array_t* arr);

/**
 * Add a string to the array
 */
void mgen_string_array_add(mgen_string_array_t* arr, char* str);

/**
 * Get string at index
 */
const char* mgen_string_array_get(mgen_string_array_t* arr, size_t index);

/**
 * Get array size
 */
size_t mgen_string_array_size(mgen_string_array_t* arr);

/**
 * Python str.split() equivalent
 * Returns an array of strings split by delimiter (whitespace if delimiter is NULL/empty)
 */
mgen_string_array_t* mgen_str_split(const char* str, const char* delimiter);

/**
 * Python str.lower() equivalent
 */
char* mgen_str_lower(const char* str);

/**
 * Python str.strip() equivalent
 */
char* mgen_str_strip(const char* str);

/**
 * String concatenation
 */
char* mgen_str_concat(const char* str1, const char* str2);

/**
 * String duplicate
 */
char* mgen_strdup(const char* str);

/**
 * Python str.join() equivalent
 * Joins strings in array with separator
 * Example: mgen_str_join(", ", ["a", "b", "c"]) -> "a, b, c"
 */
char* mgen_str_join(const char* separator, mgen_string_array_t* strings);

/**
 * Python str.replace() equivalent
 * Replaces all occurrences of old with new
 * Example: mgen_str_replace("hello world", "world", "python") -> "hello python"
 */
char* mgen_str_replace(const char* str, const char* old, const char* new_str);

/**
 * Python str.upper() equivalent
 */
char* mgen_str_upper(const char* str);

/**
 * Python str.startswith() equivalent
 */
int mgen_str_startswith(const char* str, const char* prefix);

/**
 * Python str.endswith() equivalent
 */
int mgen_str_endswith(const char* str, const char* suffix);

#endif // MGEN_LLVM_STRING_H
