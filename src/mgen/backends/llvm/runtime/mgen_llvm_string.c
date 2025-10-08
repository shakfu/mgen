/**
 * MGen LLVM Backend - String Operations Runtime Implementation
 */

#include "mgen_llvm_string.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// String array implementation
mgen_string_array_t* mgen_string_array_new(void) {
    mgen_string_array_t* arr = malloc(sizeof(mgen_string_array_t));
    if (!arr) return NULL;

    arr->strings = NULL;
    arr->count = 0;
    arr->capacity = 0;
    return arr;
}

void mgen_string_array_free(mgen_string_array_t* arr) {
    if (!arr) return;

    for (size_t i = 0; i < arr->count; i++) {
        free(arr->strings[i]);
    }
    free(arr->strings);
    free(arr);
}

void mgen_string_array_add(mgen_string_array_t* arr, char* str) {
    if (!arr) return;

    if (arr->count >= arr->capacity) {
        size_t new_capacity = arr->capacity == 0 ? 8 : arr->capacity * 2;
        char** new_strings = realloc(arr->strings, new_capacity * sizeof(char*));
        if (!new_strings) return;
        arr->strings = new_strings;
        arr->capacity = new_capacity;
    }

    arr->strings[arr->count++] = str;
}

const char* mgen_string_array_get(mgen_string_array_t* arr, size_t index) {
    if (!arr || index >= arr->count) {
        return NULL;
    }
    return arr->strings[index];
}

size_t mgen_string_array_size(mgen_string_array_t* arr) {
    return arr ? arr->count : 0;
}

char* mgen_strdup(const char* str) {
    if (!str) return NULL;

    size_t len = strlen(str);
    char* result = malloc(len + 1);
    if (!result) return NULL;

    strcpy(result, str);
    return result;
}

mgen_string_array_t* mgen_str_split(const char* str, const char* delimiter) {
    if (!str) return NULL;

    mgen_string_array_t* result = mgen_string_array_new();
    if (!result) return NULL;

    // Make a copy since strtok modifies the string
    char* str_copy = mgen_strdup(str);
    if (!str_copy) {
        mgen_string_array_free(result);
        return NULL;
    }

    char* token;
    char* saveptr = NULL;  // For thread-safe strtok_r

    // Python's split() without args splits on any whitespace
    if (!delimiter || delimiter[0] == '\0') {
        token = strtok_r(str_copy, " \t\n\r\f\v", &saveptr);
        while (token != NULL) {
            char* token_copy = mgen_strdup(token);
            if (token_copy) {
                mgen_string_array_add(result, token_copy);
            }
            token = strtok_r(NULL, " \t\n\r\f\v", &saveptr);
        }
    } else {
        token = strtok_r(str_copy, delimiter, &saveptr);
        while (token != NULL) {
            char* token_copy = mgen_strdup(token);
            if (token_copy) {
                mgen_string_array_add(result, token_copy);
            }
            token = strtok_r(NULL, delimiter, &saveptr);
        }
    }

    free(str_copy);
    return result;
}

char* mgen_str_lower(const char* str) {
    if (!str) return NULL;

    char* result = mgen_strdup(str);
    if (!result) return NULL;

    for (char* p = result; *p; p++) {
        *p = tolower((unsigned char)*p);
    }

    return result;
}

char* mgen_str_strip(const char* str) {
    if (!str) return NULL;

    // Find start (skip leading whitespace)
    while (*str && isspace((unsigned char)*str)) {
        str++;
    }

    if (!*str) {
        // String was all whitespace
        return mgen_strdup("");
    }

    // Find end (skip trailing whitespace)
    const char* end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) {
        end--;
    }

    // Calculate length and allocate
    size_t len = end - str + 1;
    char* result = malloc(len + 1);
    if (!result) return NULL;

    strncpy(result, str, len);
    result[len] = '\0';

    return result;
}

char* mgen_str_concat(const char* str1, const char* str2) {
    if (!str1 && !str2) return mgen_strdup("");
    if (!str1) return mgen_strdup(str2);
    if (!str2) return mgen_strdup(str1);

    size_t len1 = strlen(str1);
    size_t len2 = strlen(str2);
    char* result = malloc(len1 + len2 + 1);
    if (!result) return NULL;

    strcpy(result, str1);
    strcat(result, str2);

    return result;
}
