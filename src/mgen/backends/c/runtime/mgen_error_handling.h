/**
 * MGen Runtime Library - Error Handling
 *
 * Provides error handling and reporting utilities for generated C code.
 * This module handles runtime errors in a consistent, Python-like manner.
 */

#ifndef MGEN_ERROR_HANDLING_H
#define MGEN_ERROR_HANDLING_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#ifdef __cplusplus
extern "C" {
#endif

// Error codes matching common Python exceptions
typedef enum {
    MGEN_OK = 0,
    MGEN_ERROR_GENERIC = 1,
    MGEN_ERROR_MEMORY = 2,          // MemoryError
    MGEN_ERROR_INDEX = 3,           // IndexError
    MGEN_ERROR_KEY = 4,             // KeyError
    MGEN_ERROR_VALUE = 5,           // ValueError
    MGEN_ERROR_TYPE = 6,            // TypeError
    MGEN_ERROR_IO = 7,              // IOError/OSError
    MGEN_ERROR_FILE_NOT_FOUND = 8, // FileNotFoundError
    MGEN_ERROR_PERMISSION = 9,      // PermissionError
    MGEN_ERROR_RUNTIME = 10         // RuntimeError
} mgen_error_t;

// Error context structure
typedef struct {
    mgen_error_t code;
    char message[512];
    const char* file;
    int line;
    const char* function;
} mgen_error_context_t;

// Global error context (thread-local in multi-threaded environments)
extern mgen_error_context_t mgen_last_error;

/**
 * Set error with detailed context information
 */
void mgen_set_error(mgen_error_t code, const char* message,
                   const char* file, int line, const char* function);

/**
 * Set error with formatted message
 */
void mgen_set_error_fmt(mgen_error_t code, const char* file, int line,
                       const char* function, const char* format, ...);

/**
 * Get the last error code
 */
mgen_error_t mgen_get_last_error(void);

/**
 * Get the last error message
 */
const char* mgen_get_last_error_message(void);

/**
 * Clear the last error
 */
void mgen_clear_error(void);

/**
 * Check if there's a pending error
 */
int mgen_has_error(void);

/**
 * Print error information to stderr
 */
void mgen_print_error(void);

/**
 * Convert system errno to MGen error code
 */
mgen_error_t mgen_errno_to_error(int errno_val);

/**
 * Get error name as string
 */
const char* mgen_error_name(mgen_error_t code);

// Convenience macros for error handling
#define MGEN_SET_ERROR(code, msg) \
    mgen_set_error((code), (msg), __FILE__, __LINE__, __func__)

#define MGEN_SET_ERROR_FMT(code, fmt, ...) \
    mgen_set_error_fmt((code), __FILE__, __LINE__, __func__, (fmt), ##__VA_ARGS__)

#define MGEN_RETURN_IF_ERROR(expr) \
    do { \
        if ((expr) != MGEN_OK) { \
            return mgen_get_last_error(); \
        } \
    } while(0)

#define MGEN_CHECK_NULL(ptr, msg) \
    do { \
        if ((ptr) == NULL) { \
            MGEN_SET_ERROR(MGEN_ERROR_MEMORY, (msg)); \
            return MGEN_ERROR_MEMORY; \
        } \
    } while(0)

#define MGEN_CHECK_BOUNDS(index, size, msg) \
    do { \
        if ((index) < 0 || (index) >= (size)) { \
            MGEN_SET_ERROR_FMT(MGEN_ERROR_INDEX, "%s: index %d out of bounds [0, %d)", \
                               (msg), (index), (size)); \
            return MGEN_ERROR_INDEX; \
        } \
    } while(0)

#ifdef __cplusplus
}
#endif

#endif // MGEN_ERROR_HANDLING_H