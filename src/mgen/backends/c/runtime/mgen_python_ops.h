/**
 * MGen Runtime Library - Python-specific Operations
 *
 * Provides Python-specific operations that complement STC containers.
 * This module focuses on Python semantics not naturally provided by STC.
 */

#ifndef MGEN_PYTHON_OPS_H
#define MGEN_PYTHON_OPS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "mgen_error_handling.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Python built-in functions that aren't container-specific
 */

/**
 * Python bool() function
 */
int mgen_bool(const void* obj, int (*is_truthy)(const void*));

/**
 * Python bool() for integers
 */
int mgen_bool_int(int value);

/**
 * Python bool() for floats
 */
int mgen_bool_float(double value);

/**
 * Python bool() for strings (C string version)
 */
int mgen_bool_cstring(const char* str);

/**
 * Python abs() function
 */
int mgen_abs_int(int value);
double mgen_abs_float(double value);

/**
 * Python min() and max() for arrays
 */
int mgen_min_int_array(const int* arr, size_t size);
int mgen_max_int_array(const int* arr, size_t size);
double mgen_min_float_array(const double* arr, size_t size);
double mgen_max_float_array(const double* arr, size_t size);

/**
 * Python sum() for arrays
 */
int mgen_sum_int_array(const int* arr, size_t size);
double mgen_sum_float_array(const double* arr, size_t size);

/**
 * Python range() functionality
 */
typedef struct {
    int start;
    int stop;
    int step;
    int current;
} mgen_range_t;

mgen_range_t mgen_range(int stop);
mgen_range_t mgen_range_start_stop(int start, int stop);
mgen_range_t mgen_range_full(int start, int stop, int step);

int mgen_range_next(mgen_range_t* range);
int mgen_range_has_next(const mgen_range_t* range);

/**
 * Python-style string character classification
 */
int mgen_isalpha_char(char c);
int mgen_isdigit_char(char c);
int mgen_isspace_char(char c);
int mgen_isalnum_char(char c);

/**
 * Python-style string case conversion for single characters
 */
char mgen_lower_char(char c);
char mgen_upper_char(char c);

/**
 * Python ord() and chr() functions
 */
int mgen_ord(char c);
char mgen_chr(int code);

/**
 * Python-style comparison functions
 */
int mgen_cmp_int(int a, int b);
int mgen_cmp_float(double a, double b);
int mgen_cmp_string(const char* a, const char* b);

/**
 * Python-style slice object
 */
typedef struct {
    int start;
    int stop;
    int step;
    int has_start;
    int has_stop;
    int has_step;
} mgen_python_slice_t;

mgen_python_slice_t mgen_slice_new(void);
mgen_python_slice_t mgen_slice_start_stop(int start, int stop);
mgen_python_slice_t mgen_slice_full(int start, int stop, int step);

/**
 * Normalize Python slice for a given sequence length
 */
typedef struct {
    size_t start;
    size_t stop;
    size_t step;
    size_t length;
} mgen_normalized_slice_t;

mgen_error_t mgen_normalize_python_slice(const mgen_python_slice_t* slice,
                                        size_t seq_len,
                                        mgen_normalized_slice_t* result);

/**
 * Python-style exception information
 */
typedef struct {
    mgen_error_t type;
    char message[256];
    char traceback[512];
} mgen_exception_t;

extern mgen_exception_t mgen_current_exception;

void mgen_raise_exception(mgen_error_t type, const char* message);
void mgen_clear_exception(void);
int mgen_has_exception(void);
const mgen_exception_t* mgen_get_exception(void);

/**
 * Python-style assert
 */
#define mgen_assert(condition, message) \
    do { \
        if (!(condition)) { \
            mgen_raise_exception(MGEN_ERROR_RUNTIME, message); \
            return; \
        } \
    } while(0)

#define mgen_assert_return(condition, message, retval) \
    do { \
        if (!(condition)) { \
            mgen_raise_exception(MGEN_ERROR_RUNTIME, message); \
            return (retval); \
        } \
    } while(0)

/**
 * Python-style try/except simulation
 */
#define MGEN_TRY \
    do { \
        mgen_clear_exception(); \

#define MGEN_EXCEPT(error_type) \
        if (mgen_has_exception() && mgen_get_exception()->type == (error_type)) {

#define MGEN_EXCEPT_ANY \
        if (mgen_has_exception()) {

#define MGEN_FINALLY \
        } \
        if (1) {

#define MGEN_END_TRY \
        } \
    } while(0)

/**
 * Python-style truthiness testing
 */
int mgen_is_truthy_int(int value);
int mgen_is_truthy_float(double value);
int mgen_is_truthy_cstring(const char* str);
int mgen_is_truthy_pointer(const void* ptr);

/**
 * Python-style type checking
 */
typedef enum {
    MGEN_TYPE_NONE,
    MGEN_TYPE_BOOL,
    MGEN_TYPE_INT,
    MGEN_TYPE_FLOAT,
    MGEN_TYPE_STRING,
    MGEN_TYPE_LIST,
    MGEN_TYPE_DICT,
    MGEN_TYPE_SET,
    MGEN_TYPE_TUPLE
} mgen_python_type_t;

const char* mgen_type_name(mgen_python_type_t type);

/**
 * Python-style format string operations (simplified)
 */
char* mgen_format_simple(const char* template_str, const char* arg);
char* mgen_format_int(const char* template_str, int value);
char* mgen_format_float(const char* template_str, double value);

/**
 * Python zip() functionality for two arrays
 */
typedef struct {
    void* first;
    void* second;
    size_t index;
    size_t size1;
    size_t size2;
    size_t element_size1;
    size_t element_size2;
} mgen_zip_iterator_t;

mgen_zip_iterator_t mgen_zip_arrays(void* arr1, size_t size1, size_t elem_size1,
                                   void* arr2, size_t size2, size_t elem_size2);

int mgen_zip_next(mgen_zip_iterator_t* iter, void** elem1, void** elem2);

/**
 * Python-style iteration helpers
 */
typedef struct {
    size_t index;
    void* element;
} mgen_enumerate_item_t;

typedef void (*mgen_python_enumerate_callback_t)(const mgen_enumerate_item_t* item, void* userdata);

void mgen_enumerate_array(void* array, size_t size, size_t element_size,
                         mgen_python_enumerate_callback_t callback, void* userdata);

/**
 * Python print() function equivalents
 */
void print_int(int value);
void print_float(double value);
void print_string(const char* str);

// Generic print macro using C11 _Generic for type-based dispatch
#define print(x) _Generic((x), \
    int: print_int, \
    long: print_int, \
    float: print_float, \
    double: print_float, \
    char*: print_string, \
    const char*: print_string, \
    default: print_int \
)(x)

#ifdef __cplusplus
}
#endif

#endif // MGEN_PYTHON_OPS_H