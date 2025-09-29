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
#include "mgen_error_handling.h"

#ifdef __cplusplus
extern "C" {
#endif

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
 * Returns a simple string result for basic testing (simplified implementation)
 */
char* mgen_str_split(const char* str, const char* delimiter);

/**
 * Safe string duplication with error handling
 */
char* mgen_strdup(const char* str);

#ifdef __cplusplus
}
#endif

#endif // MGEN_STRING_OPS_H