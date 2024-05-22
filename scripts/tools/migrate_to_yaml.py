#!/usr/bin/env python3
"""
Utilities for migrating old code to YAML-input
"""
import functools
import inspect
import yaml
import sys

def print_params_as_yaml(key_arg=None, file_obj=sys.stdout):
    """
    A decorator that converts the parameters of a function to YAML format and prints or writes them.

    Args:
        key_arg (str): The name of the argument that will be used as the key in the YAML dictionary, or None to use the return value
        file_obj (file-like object, optional): The file-like object to write the YAML output to. Defaults to sys.stdout.

    Returns:
        The decorated function.

    Raises:
        ValueError: If the key argument is not provided in the function call.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the function signature
            sig = inspect.signature(func)
            # Bind the arguments to the function signature
            bound_arguments = sig.bind(*args, **kwargs)
            # Convert the bound arguments to a dictionary
            params = dict(bound_arguments.arguments)
            
            # Extract the value of the key_arg
            if key_arg not in params and key_arg is not None:
                raise ValueError(f"The key argument '{key_arg}' is not provided in the function call.")
            
            # Execute the function
            ret = func(*args, **kwargs)

            if key_arg is None:
                key_value = ret
            else: # key_arg is in the parameters
                key_value = params.pop(key_arg)
            # Add the function name to the parameters
            params['func'] = func.__name__
            yaml_dict = {key_value: params}
            
            # Convert the parameters dictionary to YAML format
            params_yaml = yaml.dump(yaml_dict, default_flow_style=False)
            
            # Print or write the parameters in YAML format
            file_obj.write(params_yaml)
            file_obj.write('\n\n')
        
        return wrapper
    return decorator
