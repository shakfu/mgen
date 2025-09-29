// Package mgen provides runtime support for MGen-generated Go code
// This package uses only the Go standard library to provide Python-like operations
package mgen

import (
	"fmt"
	"math"
	"reflect"
	"sort"
	"strconv"
	"strings"
)

// StringOps provides Python-like string operations
type StringOps struct{}

// Upper converts string to uppercase
func (s StringOps) Upper(str string) string {
	return strings.ToUpper(str)
}

// Lower converts string to lowercase
func (s StringOps) Lower(str string) string {
	return strings.ToLower(str)
}

// Strip removes whitespace from both ends
func (s StringOps) Strip(str string) string {
	return strings.TrimSpace(str)
}

// StripChars removes specified characters from both ends
func (s StringOps) StripChars(str, chars string) string {
	return strings.Trim(str, chars)
}

// Find returns the index of the first occurrence of substr in str, or -1 if not found
func (s StringOps) Find(str, substr string) int {
	index := strings.Index(str, substr)
	return index
}

// Replace replaces all occurrences of old with new in str
func (s StringOps) Replace(str, old, new string) string {
	return strings.ReplaceAll(str, old, new)
}

// Split splits string by delimiter
func (s StringOps) Split(str string) []string {
	return strings.Fields(str)
}

// SplitSep splits string by specific separator
func (s StringOps) SplitSep(str, sep string) []string {
	return strings.Split(str, sep)
}

// Global StringOps instance
var StrOps = StringOps{}

// BuiltinOps provides Python-like built-in functions
type BuiltinOps struct{}

// Abs returns absolute value for various numeric types
func (b BuiltinOps) Abs(x interface{}) interface{} {
	switch v := x.(type) {
	case int:
		if v < 0 {
			return -v
		}
		return v
	case int64:
		if v < 0 {
			return -v
		}
		return v
	case float64:
		return math.Abs(v)
	case float32:
		return float32(math.Abs(float64(v)))
	default:
		panic(fmt.Sprintf("abs() not supported for type %T", x))
	}
}

// Len returns length of various container types
func (b BuiltinOps) Len(x interface{}) int {
	v := reflect.ValueOf(x)
	switch v.Kind() {
	case reflect.Slice, reflect.Array, reflect.Map, reflect.String:
		return v.Len()
	default:
		panic(fmt.Sprintf("len() not supported for type %T", x))
	}
}

// Min returns minimum value from slice
func (b BuiltinOps) Min(slice interface{}) interface{} {
	v := reflect.ValueOf(slice)
	if v.Kind() != reflect.Slice || v.Len() == 0 {
		panic("min() requires non-empty slice")
	}

	min := v.Index(0).Interface()
	for i := 1; i < v.Len(); i++ {
		item := v.Index(i).Interface()
		if compareValues(item, min) < 0 {
			min = item
		}
	}
	return min
}

// Max returns maximum value from slice
func (b BuiltinOps) Max(slice interface{}) interface{} {
	v := reflect.ValueOf(slice)
	if v.Kind() != reflect.Slice || v.Len() == 0 {
		panic("max() requires non-empty slice")
	}

	max := v.Index(0).Interface()
	for i := 1; i < v.Len(); i++ {
		item := v.Index(i).Interface()
		if compareValues(item, max) > 0 {
			max = item
		}
	}
	return max
}

// Sum returns sum of numeric slice
func (b BuiltinOps) Sum(slice interface{}) interface{} {
	v := reflect.ValueOf(slice)
	if v.Kind() != reflect.Slice {
		panic("sum() requires slice")
	}

	if v.Len() == 0 {
		return 0
	}

	first := v.Index(0).Interface()
	switch first.(type) {
	case int:
		total := 0
		for i := 0; i < v.Len(); i++ {
			total += v.Index(i).Interface().(int)
		}
		return total
	case float64:
		total := 0.0
		for i := 0; i < v.Len(); i++ {
			total += v.Index(i).Interface().(float64)
		}
		return total
	default:
		panic(fmt.Sprintf("sum() not supported for type %T", first))
	}
}

// BoolValue converts various types to boolean following Python rules
func (b BuiltinOps) BoolValue(x interface{}) bool {
	if x == nil {
		return false
	}

	v := reflect.ValueOf(x)
	switch v.Kind() {
	case reflect.Bool:
		return v.Bool()
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return v.Int() != 0
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		return v.Uint() != 0
	case reflect.Float32, reflect.Float64:
		return v.Float() != 0.0
	case reflect.String:
		return v.String() != ""
	case reflect.Slice, reflect.Array, reflect.Map:
		return v.Len() > 0
	default:
		return true
	}
}

// Global BuiltinOps instance
var Builtins = BuiltinOps{}

// Range provides Python-like range functionality
type Range struct {
	Start int
	Stop  int
	Step  int
}

// NewRange creates a new range with start, stop, step
func NewRange(args ...int) Range {
	switch len(args) {
	case 1:
		return Range{Start: 0, Stop: args[0], Step: 1}
	case 2:
		return Range{Start: args[0], Stop: args[1], Step: 1}
	case 3:
		return Range{Start: args[0], Stop: args[1], Step: args[2]}
	default:
		panic("range() requires 1-3 arguments")
	}
}

// ToSlice converts range to integer slice
func (r Range) ToSlice() []int {
	if r.Step == 0 {
		panic("range() step cannot be zero")
	}

	result := []int{}
	if r.Step > 0 {
		for i := r.Start; i < r.Stop; i += r.Step {
			result = append(result, i)
		}
	} else {
		for i := r.Start; i > r.Stop; i += r.Step {
			result = append(result, i)
		}
	}
	return result
}

// ForEach executes function for each value in range
func (r Range) ForEach(fn func(int)) {
	if r.Step == 0 {
		panic("range() step cannot be zero")
	}

	if r.Step > 0 {
		for i := r.Start; i < r.Stop; i += r.Step {
			fn(i)
		}
	} else {
		for i := r.Start; i > r.Stop; i += r.Step {
			fn(i)
		}
	}
}

// ComprehensionOps provides comprehension-like operations using Go functional patterns
type ComprehensionOps struct{}

// ListComprehension creates slice by applying transform function to each element
func (c ComprehensionOps) ListComprehension(source interface{}, transform func(interface{}) interface{}) []interface{} {
	result := []interface{}{}

	if r, ok := source.(Range); ok {
		r.ForEach(func(i int) {
			result = append(result, transform(i))
		})
		return result
	}

	v := reflect.ValueOf(source)
	if v.Kind() == reflect.Slice {
		for i := 0; i < v.Len(); i++ {
			item := v.Index(i).Interface()
			result = append(result, transform(item))
		}
	}
	return result
}

// ListComprehensionWithFilter creates slice with filtering
func (c ComprehensionOps) ListComprehensionWithFilter(source interface{}, transform func(interface{}) interface{}, filter func(interface{}) bool) []interface{} {
	result := []interface{}{}

	if r, ok := source.(Range); ok {
		r.ForEach(func(i int) {
			if filter(i) {
				result = append(result, transform(i))
			}
		})
		return result
	}

	v := reflect.ValueOf(source)
	if v.Kind() == reflect.Slice {
		for i := 0; i < v.Len(); i++ {
			item := v.Index(i).Interface()
			if filter(item) {
				result = append(result, transform(item))
			}
		}
	}
	return result
}

// DictComprehension creates map by applying transform function
func (c ComprehensionOps) DictComprehension(source interface{}, transform func(interface{}) (interface{}, interface{})) map[interface{}]interface{} {
	result := make(map[interface{}]interface{})

	if r, ok := source.(Range); ok {
		r.ForEach(func(i int) {
			k, v := transform(i)
			result[k] = v
		})
		return result
	}

	v := reflect.ValueOf(source)
	if v.Kind() == reflect.Slice {
		for i := 0; i < v.Len(); i++ {
			item := v.Index(i).Interface()
			k, val := transform(item)
			result[k] = val
		}
	}
	return result
}

// SetComprehension creates map[T]bool set by applying transform function
func (c ComprehensionOps) SetComprehension(source interface{}, transform func(interface{}) interface{}) map[interface{}]bool {
	result := make(map[interface{}]bool)

	if r, ok := source.(Range); ok {
		r.ForEach(func(i int) {
			result[transform(i)] = true
		})
		return result
	}

	v := reflect.ValueOf(source)
	if v.Kind() == reflect.Slice {
		for i := 0; i < v.Len(); i++ {
			item := v.Index(i).Interface()
			result[transform(item)] = true
		}
	}
	return result
}

// Global ComprehensionOps instance
var Comprehensions = ComprehensionOps{}

// Helper functions

// compareValues compares two values for ordering
func compareValues(a, b interface{}) int {
	va := reflect.ValueOf(a)
	vb := reflect.ValueOf(b)

	if va.Type() != vb.Type() {
		panic("cannot compare different types")
	}

	switch va.Kind() {
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		ai, bi := va.Int(), vb.Int()
		if ai < bi {
			return -1
		} else if ai > bi {
			return 1
		}
		return 0
	case reflect.Float32, reflect.Float64:
		af, bf := va.Float(), vb.Float()
		if af < bf {
			return -1
		} else if af > bf {
			return 1
		}
		return 0
	case reflect.String:
		as, bs := va.String(), vb.String()
		if as < bs {
			return -1
		} else if as > bs {
			return 1
		}
		return 0
	default:
		panic(fmt.Sprintf("comparison not supported for type %T", a))
	}
}

// ToStr converts various types to string (Python str() equivalent)
func ToStr(x interface{}) string {
	if x == nil {
		return "None"
	}

	switch v := x.(type) {
	case string:
		return v
	case bool:
		if v {
			return "True"
		}
		return "False"
	case int, int8, int16, int32, int64, uint, uint8, uint16, uint32, uint64:
		return fmt.Sprintf("%d", v)
	case float32, float64:
		return fmt.Sprintf("%g", v)
	default:
		return fmt.Sprintf("%v", v)
	}
}

// Print provides Python-like print function
func Print(args ...interface{}) {
	strs := make([]string, len(args))
	for i, arg := range args {
		strs[i] = ToStr(arg)
	}
	fmt.Println(strings.Join(strs, " "))
}