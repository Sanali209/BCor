import os
import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")

class PathNormalizer:
    """Utilities for standardized path handling across different OS versions.
    
    Provides tools to normalize path casing and formatting, and a decorator
    to automatically apply these normalizations to function arguments.
    """
    
    @staticmethod
    def norm(path: str) -> str:
        """Normalize path casing and absolute formatting.
        
        Args:
            path: The path string to normalize.
            
        Returns:
            The normalized absolute path with standardized casing.
        """
        if not path:
            return path
        # Use normcase for Windows compatibility (lowercases on Windows)
        # and abspath for consistent root prefixing.
        return os.path.normcase(os.path.abspath(path))

    @classmethod
    def normalize_args(cls, *arg_names: str):
        """Decorator to automatically normalize specific arguments as paths.
        
        Args:
            *arg_names: Names of the arguments to be normalized.
            
        Returns:
            A decorator function.
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs):
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                for name in arg_names:
                    if name in bound_args.arguments:
                        val = bound_args.arguments[name]
                        if isinstance(val, str):
                            bound_args.arguments[name] = cls.norm(val)
                        elif isinstance(val, list):
                            bound_args.arguments[name] = [
                                cls.norm(v) if isinstance(v, str) else v 
                                for v in val
                            ]
                
                return func(*bound_args.args, **bound_args.kwargs)
            return wrapper
        return decorator
