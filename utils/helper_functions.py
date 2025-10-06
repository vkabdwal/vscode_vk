def example_helper():
    """Example helper function"""
    return "This is a helper function!" 

def add_numbers(a, b):
    return a + b

def reverse_string(s):
    """Function to reverse a string."""
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]

def factorial(n): # VK: by recursion
    """Function to calculate factorial of a number."""
    if n ==0 or n == 1:
        return 1
    else:
        return n * check(n - 1)