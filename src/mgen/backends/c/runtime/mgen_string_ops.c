/**
 * MGen Runtime Library - String Operations Implementation
 */

#include "mgen_string_ops.h"

// String array implementation
mgen_string_array_t* mgen_string_array_new(void) {
    mgen_string_array_t* arr = malloc(sizeof(mgen_string_array_t));
    if (!arr) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate string array");
        return NULL;
    }

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

mgen_error_t mgen_string_array_add(mgen_string_array_t* arr, char* str) {
    if (!arr) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String array is NULL");
        return MGEN_ERROR_VALUE;
    }

    if (arr->count >= arr->capacity) {
        size_t new_capacity = arr->capacity == 0 ? 8 : arr->capacity * 2;
        char** new_strings = realloc(arr->strings, new_capacity * sizeof(char*));
        if (!new_strings) {
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to resize string array");
            return MGEN_ERROR_MEMORY;
        }
        arr->strings = new_strings;
        arr->capacity = new_capacity;
    }

    arr->strings[arr->count++] = str;
    return MGEN_OK;
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

char* mgen_join(const char* delimiter, mgen_string_array_t* strings) {
    if (!strings || strings->count == 0) {
        return mgen_strdup("");
    }

    if (!delimiter) delimiter = "";

    // Calculate total length needed
    size_t total_len = 0;
    size_t delim_len = strlen(delimiter);

    for (size_t i = 0; i < strings->count; i++) {
        if (strings->strings[i]) {
            total_len += strlen(strings->strings[i]);
        }
        if (i < strings->count - 1) {
            total_len += delim_len;
        }
    }

    char* result = malloc(total_len + 1);
    if (!result) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for joined string");
        return NULL;
    }

    result[0] = '\0';
    for (size_t i = 0; i < strings->count; i++) {
        if (strings->strings[i]) {
            strcat(result, strings->strings[i]);
        }
        if (i < strings->count - 1) {
            strcat(result, delimiter);
        }
    }

    return result;
}

char* mgen_strdup(const char* str) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

    size_t len = strlen(str);
    char* result = malloc(len + 1);
    if (!result) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for string");
        return NULL;
    }

    strcpy(result, str);
    return result;
}

char* mgen_str_upper(const char* str) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

    char* result = mgen_strdup(str);
    if (!result) return NULL;

    for (char* p = result; *p; p++) {
        *p = toupper((unsigned char)*p);
    }

    return result;
}

char* mgen_str_lower(const char* str) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

    char* result = mgen_strdup(str);
    if (!result) return NULL;

    for (char* p = result; *p; p++) {
        *p = tolower((unsigned char)*p);
    }

    return result;
}

char* mgen_str_strip(const char* str) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

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
    if (!result) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for string");
        return NULL;
    }

    strncpy(result, str, len);
    result[len] = '\0';

    return result;
}

char* mgen_str_strip_chars(const char* str, const char* chars) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

    if (!chars || !*chars) {
        return mgen_str_strip(str);
    }

    // Find start (skip leading chars)
    while (*str && strchr(chars, *str)) {
        str++;
    }

    if (!*str) {
        // String was all strip chars
        return mgen_strdup("");
    }

    // Find end (skip trailing chars)
    const char* end = str + strlen(str) - 1;
    while (end > str && strchr(chars, *end)) {
        end--;
    }

    // Calculate length and allocate
    size_t len = end - str + 1;
    char* result = malloc(len + 1);
    if (!result) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for string");
        return NULL;
    }

    strncpy(result, str, len);
    result[len] = '\0';

    return result;
}

int mgen_str_find(const char* str, const char* substring) {
    if (!str || !substring) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String or substring is NULL");
        return -1;
    }

    const char* found = strstr(str, substring);
    if (found) {
        return (int)(found - str);
    }

    return -1;  // Not found
}

char* mgen_str_replace(const char* str, const char* old_str, const char* new_str) {
    if (!str || !old_str || !new_str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String arguments cannot be NULL");
        return NULL;
    }

    size_t old_len = strlen(old_str);
    size_t new_len = strlen(new_str);

    if (old_len == 0) {
        return mgen_strdup(str);  // Can't replace empty string
    }

    // Count occurrences to calculate result size
    const char* pos = str;
    int count = 0;
    while ((pos = strstr(pos, old_str)) != NULL) {
        count++;
        pos += old_len;
    }

    if (count == 0) {
        return mgen_strdup(str);  // No replacements needed
    }

    // Calculate result size
    size_t result_len = strlen(str) - count * old_len + count * new_len;
    char* result = malloc(result_len + 1);
    if (!result) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for string");
        return NULL;
    }

    // Build result string
    char* dest = result;
    const char* src = str;

    while ((pos = strstr(src, old_str)) != NULL) {
        // Copy part before match
        size_t prefix_len = pos - src;
        strncpy(dest, src, prefix_len);
        dest += prefix_len;

        // Copy replacement
        strcpy(dest, new_str);
        dest += new_len;

        // Move past the match
        src = pos + old_len;
    }

    // Copy remaining part
    strcpy(dest, src);

    return result;
}

char* mgen_str_split(const char* str, const char* delimiter) {
    if (!str) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "String is NULL");
        return NULL;
    }

    // Simplified implementation - just return the first token for basic testing
    // In a full implementation, this would return an array of strings
    char* str_copy = mgen_strdup(str);
    if (!str_copy) return NULL;

    char* token;
    if (!delimiter) {
        // Split on whitespace
        token = strtok(str_copy, " \t\n\r\f\v");
    } else {
        // Split on delimiter
        token = strtok(str_copy, delimiter);
    }

    if (token) {
        char* result = mgen_strdup(token);
        free(str_copy);
        return result;
    } else {
        free(str_copy);
        return mgen_strdup("");
    }
}