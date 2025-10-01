# load the util and helper functions
from utils.config_loader import load_config
from utils import helper_functions

# load necessary libraries
import pandas as pd
import numpy as np

config = load_config('settings.yml')
print(config)

# Q-1 
# function to add two numbers
print("The sum is:", helper_functions.add_numbers(3, 4))

# Q-2 
string_input = "Hello, World!"
print("Reversed string:", helper_functions.reverse_string(string_input))

# Q-3
# check if a string is a palindrome
helper_functions.is_palindrome(string_input)

# Q-4
print("Factorial of 5 is:", helper_functions.factorial(5))

# Q-5 - How would you count the occurrences of each element in a list
list_a = [1, 2, 3, 4, 5, 1, 2, 3, 3]
list_b = set(list_a)
for i in list_b:
    print(f"Count of {i} in list_a: {list_a.count(i)}")

# Q-6 - How would you find the maximum and minimum values in a list
max_value = max(list_a) 
min_value = min(list_a)
print(f"Maximum value in list_a: {max_value}")
print(f"Minimum value in list_a: {min_value}")

# Q-7 - How would you sort a list in ascending order
sorted_list = sorted(list_a)        
print("Sorted list in ascending order:", sorted_list)

# Q-8 - How would you remove duplicates from a list
unique_list = list(set(list_a))         

# Q-9 - How would you merge two dictionaries
dict_a = {'a': 1, 'b': 2}       
dict_b = {'b': 3, 'c': 4}
merged_dict = {**dict_a, **dict_b}
print("Merged dictionary:", merged_dict)

# Q-10 - How would you find the intersection of two lists
list_x = [1, 2, 3, 4]           
list_y = [3, 4, 5, 6]
intersection = list(set(list_x) & set(list_y))  
print("Intersection of list_x and list_y:", intersection)

# Q-11 - How would you check if a key exists in a dictionary
dict_c = {'x': 10, 'y': 20}
key_to_check = 'x'
try:
    value = dict_c[key_to_check]
    print(f"Key '{key_to_check}' exists in dict_c.")
except KeyError:
    print(f"Key '{key_to_check}' does not exist in dict_c.")  

# Q-12 - How would you convert a string to lowercase
string_to_convert = "Hello, World!"     
lowercase_string = string_to_convert.lower()
print("Lowercase string:", lowercase_string)

# Q-13 - How would you convert a dataframe column name to lowercase 
df = pd.DataFrame({'Column1': [1, 2, 3], 'Column2': [4, 5, 6]})
df.columns = [col.lower() for col in df.columns]    
print("DataFrame with lowercase column names:\n", df)

# Q-14 - How would you check if a string contains only digits
string_with_digits = "12345"    
string_with_non_digits = "123a45"
print(f"Does '{string_with_digits}' contain only digits? {string_with_digits.isdigit()}")
                                                          
# Q-15 - How would you check if a string contains only alphabetic characters
string_with_alpha = "HelloWorld"
string_with_non_alpha = "Hello123"
print(f"Does '{string_with_alpha}' contain only alphabetic characters? {string_with_alpha.isalpha()}")

# Q-16 -  Check if Two Strings are Anagrams of Each Other.
def are_anagrams(str1, str2):
    """Check if two strings are anagrams of each other."""
    return sorted(str1) == sorted(str2) 
print("Are 'listen' and 'silent' anagrams?", are_anagrams("listen", "silent"))

# Q-17 - Find the median of two sorted arrays of different sizes    
def find_median_sorted_arrays(nums1, nums2):
    """Find the median of two sorted arrays."""
    merged = sorted(nums1 + nums2)
    n = len(merged)
    if n % 2 == 0:
        return (merged[n // 2 - 1] + merged[n // 2]) / 2
    else:
        return merged[n // 2]
print("Median of [1, 3] and [2]:", find_median_sorted_arrays([1, 3], [2]))

# Q-18 - How to convert all the column names of a dataframe to lowercase inplace
df.columns = [col.lower() for col in df.columns]


