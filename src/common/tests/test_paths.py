import pytest
import os
from src.common.paths import PathNormalizer

def test_path_normalization():
    """Verify that PathNormalizer correctly handles Windows/Linux paths."""
    # Test absolute normalization
    path = "C:/Users/Test/../Data"
    norm_path = PathNormalizer.norm(path)
    
    expected = os.path.normcase(os.path.abspath(path))
    assert norm_path == expected
    assert os.path.isabs(norm_path)

def test_normalize_args_decorator():
    """Verify that the normalize_args decorator working correctly."""
    @PathNormalizer.normalize_args('p1', 'p2')
    async def sample_func(p1, p2, other):
        return p1, p2, other
    
    # Mocking async run for decorator test
    import asyncio
    p1 = "dir/sub"
    p2 = ["f1", "f2"]
    other = "stay"
    
    # We need to run it in a loop if it's async, but PathNormalizer doesn't care about async
    # Let's make it sync for simpler test if path normalizer supports it
    
    @PathNormalizer.normalize_args('p')
    def sync_func(p):
        return p
    
    res = sync_func(p1)
    assert res == PathNormalizer.norm(p1)
