import yaml
import os

import yaml
import os

def load_config(file_name=None, config_dir=r'D:\Github\config'):
    """
    Load a YAML configuration file from the config folder.
    
    Args:
        file_name (str, optional): Name of the YAML file to load (e.g., 'settings.yml').
                                  If None, returns an empty dict.
        config_dir (str, optional): Path to the config folder. Defaults to project config path.
    
    Returns:
        dict: Parsed configuration data, or empty dict if loading fails or file_name is None.
    """
    if file_name is None:
        print("No configuration file specified.")
        return {}

    config_path = os.path.join(config_dir, file_name)
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Error: {file_name} not found in {config_dir} folder.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_name}: {e}")
        return {}