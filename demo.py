from utils.config_loader import load_config
from utils.helper_functions import example_helper
print(load_config()) # Prints the YAML content as a dictionary
print(example_helper()) # Prints "This is a helper function!"

import pandas as pd
import numpy as np


# function to add two numbers
def add(a, b):
    return a + b    
add(3,4)
print("The sum is:", add(3, 4))


