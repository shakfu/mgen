/**
 * MGen Runtime Library - String Operations
 *
 * Provides C implementations of common Python string operations.
 * These functions handle memory management and error reporting automatically.
 */

#ifndef MGEN_STRING_OPS_H
#define MGEN_STRING_OPS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include "mgen_error_handling.h"

#ifdef __cplusplus
extern "C" {
#endif

// String array structure for storing multiple strings
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
 * Free a string array and all its strings
 */
void mgen_string_array_free(mgen_string_array_t* arr);

/**
 * Add a string to the array (takes ownership of the string)
 */
mgen_error_t mgen_string_array_add(mgen_string_array_t* arr, char* str);

/**
 * Get string at index (returns NULL if out of bounds)
 */
const char* mgen_string_array_get(mgen_string_array_t* arr, size_t index);

/**
 * Get the number of strings in the array
 */
size_t mgen_string_array_size(mgen_string_array_t* arr);

/**
 * Python str.join() equivalent
 * Joins strings in array with delimiter (caller must free result)
 */
char* mgen_join(const char* delimiter, mgen_string_array_t* strings);

/**
 * Python str.upper() equivalent
 * Returns a new uppercase string (caller must free)
 */
char* mgen_str_upper(const char* str);

/**
 * Python str.lower() equivalent
 * Returns a new lowercase string (caller must free)
 */
char* mgen_str_lower(const char* str);

/**
 * Python str.strip() equivalent
 * Returns a new string with leading/trailing whitespace removed (caller must free)
 */
char* mgen_str_strip(const char* str);

/**
 * Python str.strip(chars) equivalent
 * Returns a new string with leading/trailing chars removed (caller must free)
 */
char* mgen_str_strip_chars(const char* str, const char* chars);

/**
 * Python str.find() equivalent
 * Returns index of substring or -1 if not found
 */
int mgen_str_find(const char* str, const char* substring);

/**
 * Python str.replace() equivalent
 * Returns a new string with all occurrences replaced (caller must free)
 */
char* mgen_str_replace(const char* str, const char* old_str, const char* new_str);

/**
 * Python str.split() equivalent
 * Returns an array of strings split by delimiter (whitespace if NULL)
 */
mgen_string_array_t* mgen_str_split(const char* str, const char* delimiter);

/**
 * Safe string duplication with error handling
 */
char* mgen_strdup(const char* str);

/**
 * Convert integer to string (caller must free result)
 * Used for f-string formatting
 */
char* mgen_int_to_string(int value);

/**
 * Convert float to string (caller must free result)
 * Used for f-string formatting
 */
char* mgen_float_to_string(double value);

/**
 * Convert boolean to string (returns "true" or "false")
 * Used for f-string formatting (does NOT need to be freed - returns static string)
 */
const char* mgen_bool_to_string(bool value);

/**
 * F-string sprintf helper - formats a string with variable arguments
 * Usage: mgen_sprintf_string("Hello %s, count: %s", name, int_str)
 * Returns allocated string (caller must free)
 */
char* mgen_sprintf_string(const char* format, ...);

/**
 * Concatenate two strings (returns allocated string, caller must free)
 * Used for Python's + operator with strings
 */
char* mgen_str_concat(const char* str1, const char* str2);

#ifdef __cplusplus
}
#endif

#endif // MGEN_STRING_OPS_H