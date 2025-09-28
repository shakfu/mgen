/**
 * MGen Runtime Library - Error Handling Implementation
 */

#include "mgen_error_handling.h"
#include <stdarg.h>

// Global error context
mgen_error_context_t mgen_last_error = {MGEN_OK, "", NULL, 0, NULL};

void mgen_set_error(mgen_error_t code, const char* message,
                   const char* file, int line, const char* function) {
    mgen_last_error.code = code;
    mgen_last_error.file = file;
    mgen_last_error.line = line;
    mgen_last_error.function = function;

    if (message) {
        strncpy(mgen_last_error.message, message, sizeof(mgen_last_error.message) - 1);
        mgen_last_error.message[sizeof(mgen_last_error.message) - 1] = '\0';
    } else {
        mgen_last_error.message[0] = '\0';
    }
}

void mgen_set_error_fmt(mgen_error_t code, const char* file, int line,
                       const char* function, const char* format, ...) {
    mgen_last_error.code = code;
    mgen_last_error.file = file;
    mgen_last_error.line = line;
    mgen_last_error.function = function;

    if (format) {
        va_list args;
        va_start(args, format);
        vsnprintf(mgen_last_error.message, sizeof(mgen_last_error.message), format, args);
        va_end(args);
    } else {
        mgen_last_error.message[0] = '\0';
    }
}

mgen_error_t mgen_get_last_error(void) {
    return mgen_last_error.code;
}

const char* mgen_get_last_error_message(void) {
    return mgen_last_error.message;
}

void mgen_clear_error(void) {
    mgen_last_error.code = MGEN_OK;
    mgen_last_error.message[0] = '\0';
    mgen_last_error.file = NULL;
    mgen_last_error.line = 0;
    mgen_last_error.function = NULL;
}

int mgen_has_error(void) {
    return mgen_last_error.code != MGEN_OK;
}

void mgen_print_error(void) {
    if (mgen_has_error()) {
        fprintf(stderr, "MGen Runtime Error [%s]: %s\n",
                mgen_error_name(mgen_last_error.code),
                mgen_last_error.message);

        if (mgen_last_error.file && mgen_last_error.function) {
            fprintf(stderr, "  at %s:%d in %s()\n",
                    mgen_last_error.file,
                    mgen_last_error.line,
                    mgen_last_error.function);
        }
    }
}

mgen_error_t mgen_errno_to_error(int errno_val) {
    switch (errno_val) {
        case ENOMEM:
            return MGEN_ERROR_MEMORY;
        case ENOENT:
            return MGEN_ERROR_FILE_NOT_FOUND;
        case EACCES:
        case EPERM:
            return MGEN_ERROR_PERMISSION;
        case EIO:
            return MGEN_ERROR_IO;
        case EINVAL:
            return MGEN_ERROR_VALUE;
        default:
            return MGEN_ERROR_RUNTIME;
    }
}

const char* mgen_error_name(mgen_error_t code) {
    switch (code) {
        case MGEN_OK:
            return "OK";
        case MGEN_ERROR_GENERIC:
            return "GenericError";
        case MGEN_ERROR_MEMORY:
            return "MemoryError";
        case MGEN_ERROR_INDEX:
            return "IndexError";
        case MGEN_ERROR_KEY:
            return "KeyError";
        case MGEN_ERROR_VALUE:
            return "ValueError";
        case MGEN_ERROR_TYPE:
            return "TypeError";
        case MGEN_ERROR_IO:
            return "IOError";
        case MGEN_ERROR_FILE_NOT_FOUND:
            return "FileNotFoundError";
        case MGEN_ERROR_PERMISSION:
            return "PermissionError";
        case MGEN_ERROR_RUNTIME:
            return "RuntimeError";
        default:
            return "UnknownError";
    }
}