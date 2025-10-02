/**
 * MGen Runtime Library - File I/O Operations Implementation
 */

#include "mgen_file_ops.h"
#include "mgen_string_ops.h"
#include <unistd.h>

// Platform-specific includes for path operations
#ifdef _WIN32
    #include <windows.h>
    #define PATH_SEPARATOR "\\"
#else
    #include <libgen.h>
    #define PATH_SEPARATOR "/"
#endif

mgen_file_t* mgen_open(const char* filename, const char* mode) {
    if (!filename || !mode) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Filename or mode is NULL");
        return NULL;
    }

    mgen_file_t* file = malloc(sizeof(mgen_file_t));
    if (!file) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate file handle");
        return NULL;
    }

    file->file = fopen(filename, mode);
    if (!file->file) {
        mgen_error_t error = mgen_errno_to_error(errno);
        MGEN_SET_ERROR_FMT(error, "Failed to open file '%s': %s", filename, strerror(errno));
        free(file);
        return NULL;
    }

    file->filename = mgen_strdup(filename);
    file->mode = mgen_strdup(mode);
    file->is_open = 1;

    if (!file->filename || !file->mode) {
        fclose(file->file);
        free(file->filename);
        free(file->mode);
        free(file);
        return NULL;
    }

    return file;
}

mgen_error_t mgen_close(mgen_file_t* file) {
    if (!file) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "File handle is NULL");
        return MGEN_ERROR_VALUE;
    }

    if (file->is_open && file->file) {
        if (fclose(file->file) != 0) {
            mgen_error_t error = mgen_errno_to_error(errno);
            MGEN_SET_ERROR_FMT(error, "Failed to close file '%s': %s",
                               file->filename, strerror(errno));
            return error;
        }
        file->is_open = 0;
    }

    free(file->filename);
    free(file->mode);
    free(file);

    return MGEN_OK;
}

char* mgen_read(mgen_file_t* file, size_t size) {
    if (!file || !file->is_open) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid or closed file handle");
        return NULL;
    }

    if (size == 0) {
        // Read entire file
        fseek(file->file, 0, SEEK_END);
        long file_size = ftell(file->file);
        if (file_size < 0) {
            MGEN_SET_ERROR(MGEN_ERROR_IO, "Failed to get file size");
            return NULL;
        }
        fseek(file->file, 0, SEEK_SET);
        size = (size_t)file_size;
    }

    char* buffer = malloc(size + 1);
    if (!buffer) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate read buffer");
        return NULL;
    }

    size_t bytes_read = fread(buffer, 1, size, file->file);
    if (ferror(file->file)) {
        MGEN_SET_ERROR(MGEN_ERROR_IO, "Error reading from file");
        free(buffer);
        return NULL;
    }

    buffer[bytes_read] = '\0';
    return buffer;
}

char* mgen_readline(mgen_file_t* file) {
    if (!file || !file->is_open) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid or closed file handle");
        return NULL;
    }

    size_t capacity = 128;
    char* line = malloc(capacity);
    if (!line) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate line buffer");
        return NULL;
    }

    size_t length = 0;
    int c;

    while ((c = fgetc(file->file)) != EOF) {
        if (length >= capacity - 1) {
            capacity *= 2;
            char* new_line = realloc(line, capacity);
            if (!new_line) {
                MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to resize line buffer");
                free(line);
                return NULL;
            }
            line = new_line;
        }

        line[length++] = (char)c;
        if (c == '\n') break;
    }

    if (length == 0 && c == EOF) {
        free(line);
        return NULL; // End of file
    }

    line[length] = '\0';
    return line;
}

mgen_string_array_t* mgen_readlines(mgen_file_t* file) {
    if (!file || !file->is_open) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid or closed file handle");
        return NULL;
    }

    mgen_string_array_t* lines = mgen_string_array_new();
    if (!lines) return NULL;

    char* line;
    while ((line = mgen_readline(file)) != NULL) {
        if (mgen_string_array_add(lines, line) != MGEN_OK) {
            free(line);
            mgen_string_array_free(lines);
            return NULL;
        }
    }

    return lines;
}

int mgen_write(mgen_file_t* file, const char* data) {
    if (!file || !file->is_open) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid or closed file handle");
        return -1;
    }

    if (!data) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Data is NULL");
        return -1;
    }

    size_t len = strlen(data);
    size_t written = fwrite(data, 1, len, file->file);

    if (written < len) {
        MGEN_SET_ERROR(MGEN_ERROR_IO, "Failed to write complete data to file");
        return -1;
    }

    return (int)written;
}

mgen_error_t mgen_writelines(mgen_file_t* file, mgen_string_array_t* lines) {
    if (!file || !file->is_open) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Invalid or closed file handle");
        return MGEN_ERROR_VALUE;
    }

    if (!lines) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Lines array is NULL");
        return MGEN_ERROR_VALUE;
    }

    for (size_t i = 0; i < lines->count; i++) {
        if (lines->strings[i]) {
            if (mgen_write(file, lines->strings[i]) < 0) {
                return mgen_get_last_error();
            }
        }
    }

    return MGEN_OK;
}

int mgen_exists(const char* path) {
    if (!path) return 0;

    struct stat st;
    return stat(path, &st) == 0;
}

int mgen_isfile(const char* path) {
    if (!path) return 0;

    struct stat st;
    if (stat(path, &st) != 0) return 0;
    return S_ISREG(st.st_mode);
}

int mgen_isdir(const char* path) {
    if (!path) return 0;

    struct stat st;
    if (stat(path, &st) != 0) return 0;
    return S_ISDIR(st.st_mode);
}

long mgen_getsize(const char* path) {
    if (!path) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Path is NULL");
        return -1;
    }

    struct stat st;
    if (stat(path, &st) != 0) {
        mgen_error_t error = mgen_errno_to_error(errno);
        MGEN_SET_ERROR_FMT(error, "Failed to get file size for '%s': %s", path, strerror(errno));
        return -1;
    }

    return (long)st.st_size;
}

char* mgen_basename(const char* path) {
    if (!path) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Path is NULL");
        return NULL;
    }

    // Find the last occurrence of path separator
    const char* last_sep = strrchr(path, '/');
#ifdef _WIN32
    const char* last_sep_win = strrchr(path, '\\');
    if (last_sep_win > last_sep) last_sep = last_sep_win;
#endif

    const char* basename = last_sep ? last_sep + 1 : path;
    return mgen_strdup(basename);
}

char* mgen_dirname(const char* path) {
    if (!path) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Path is NULL");
        return NULL;
    }

    // Find the last occurrence of path separator
    const char* last_sep = strrchr(path, '/');
#ifdef _WIN32
    const char* last_sep_win = strrchr(path, '\\');
    if (last_sep_win > last_sep) last_sep = last_sep_win;
#endif

    if (!last_sep) {
        return mgen_strdup(".");
    }

    if (last_sep == path) {
        return mgen_strdup(PATH_SEPARATOR);
    }

    size_t dir_len = last_sep - path;
    char* dirname = malloc(dir_len + 1);
    if (!dirname) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for dirname");
        return NULL;
    }

    memcpy(dirname, path, dir_len);
    dirname[dir_len] = '\0';

    return dirname;
}

char* mgen_path_join(const char* path1, const char* path2) {
    if (!path1 || !path2) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Path component is NULL");
        return NULL;
    }

    size_t len1 = strlen(path1);
    size_t len2 = strlen(path2);
    int need_separator = (len1 > 0 && path1[len1-1] != '/' && path1[len1-1] != '\\');

    size_t total_len = len1 + len2 + (need_separator ? 1 : 0);
    char* result = malloc(total_len + 1);
    if (!result) {
        MGEN_SET_ERROR(MGEN_ERROR_MEMORY, "Failed to allocate memory for path join");
        return NULL;
    }

    strcpy(result, path1);
    if (need_separator) {
        strcat(result, PATH_SEPARATOR);
    }
    strcat(result, path2);

    return result;
}

char* mgen_read_file(const char* filename) {
    mgen_file_t* file = mgen_open(filename, "r");
    if (!file) return NULL;

    char* content = mgen_read(file, 0);
    mgen_close(file);

    return content;
}

mgen_error_t mgen_write_file(const char* filename, const char* content) {
    mgen_file_t* file = mgen_open(filename, "w");
    if (!file) return mgen_get_last_error();

    if (mgen_write(file, content) < 0) {
        mgen_error_t error = mgen_get_last_error();
        mgen_close(file);
        return error;
    }

    return mgen_close(file);
}

mgen_error_t mgen_append_file(const char* filename, const char* content) {
    mgen_file_t* file = mgen_open(filename, "a");
    if (!file) return mgen_get_last_error();

    if (mgen_write(file, content) < 0) {
        mgen_error_t error = mgen_get_last_error();
        mgen_close(file);
        return error;
    }

    return mgen_close(file);
}

mgen_error_t mgen_with_file(const char* filename, const char* mode,
                           mgen_file_operation_t operation, void* userdata) {
    if (!operation) {
        MGEN_SET_ERROR(MGEN_ERROR_VALUE, "Operation function is NULL");
        return MGEN_ERROR_VALUE;
    }

    mgen_file_t* file = mgen_open(filename, mode);
    if (!file) return mgen_get_last_error();

    mgen_error_t result = operation(file, userdata);

    mgen_error_t close_result = mgen_close(file);
    return (result != MGEN_OK) ? result : close_result;
}
