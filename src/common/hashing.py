"""Persistent hashing and caching services."""
from __future__ import annotations

import functools
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Callable, TypeVar

import diskcache as dc

T = TypeVar("T")

logger = logging.getLogger(__name__)


class HashingService:
    """Service for generating stable hashes and providing persistent caching.
    
    Ported and modernized from legacy appGlue/hashingService.py.
    """

    def __init__(self, cache_dir: str | Path = ".cache/hashing"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = dc.Cache(str(self.cache_dir))

    def generate_key(self, func: Callable, *args: Any, **kwargs: Any) -> str:
        """Generate a stable hash key for a function call.
        
        Args:
            func: The function being called.
            args: Positional arguments.
            kwargs: Keyword arguments.
            
        Returns:
            A hex string representig the unique call signature.
        """
        sha = hashlib.sha256()
        # Include function's qualified name to prevent collisions between different functions with same args
        sha.update(f"{func.__module__}.{func.__qualname__}".encode())

        # Serialize arguments. 
        # Note: We use repr() here as a simple way to get a stable string for most Python objects.
        # For complex domain objects, they should implement a stable __repr__ or be pydantic models.
        for arg in args:
            sha.update(repr(arg).encode())
        for k, v in sorted(kwargs.items()):
            sha.update(f"{k}={repr(v)}".encode())
            
        return sha.hexdigest()

    def persistent_cache(self, hashtable: str = "default"):
        """Decorator to add persistent disk-caching to a function.
        
        Args:
            hashtable: Optional sub-partition for the cache.
            
        Returns:
            A decorator that wraps the function with caching logic.
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                # Generate key
                key = self.generate_key(func, *args, **kwargs)
                
                # Check cache
                if key in self._cache:
                    logger.debug(f"Cache hit for {func.__name__} (key: {key[:8]}...)")
                    return self._cache[key]
                
                # Execute and store
                result = func(*args, **kwargs)
                self._cache[key] = result
                logger.debug(f"Cache miss for {func.__name__}. Stored result.")
                return result
            
            # For async functions, we need an async wrapper
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                key = self.generate_key(func, *args, **kwargs)
                
                if key in self._cache:
                    logger.debug(f"Cache hit (async) for {func.__name__}")
                    return self._cache[key]
                
                result = await func(*args, **kwargs)
                self._cache[key] = result
                return result

            import asyncio
            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

        return decorator

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("Hashing cache cleared.")
