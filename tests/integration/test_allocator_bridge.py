import sys
import os
import pytest
from unittest.mock import MagicMock

# Add legacy path to sys.path
# The SLM package is inside sanali209/Python
legacy_parent_path = os.path.abspath(os.path.join(os.getcwd(), "src", "legacy_to_port", "sanali209", "Python"))
if legacy_parent_path not in sys.path:
    sys.path.append(legacy_parent_path)

from SLM.appGlue.core import Allocator, Service, Resource

class MockLegacyService(Service):
    def __init__(self):
        super().__init__()
        self.value = "legacy"

@pytest.fixture
def clean_allocator():
    """Clears Allocator resources before/after test."""
    original_resources = Allocator.res.resources[:]
    original_type_res = Allocator.res.type_res.copy()
    Allocator.res.resources = []
    Allocator.res.type_res = {}
    yield Allocator
    Allocator.res.resources = original_resources
    Allocator.res.type_res = original_type_res

def test_legacy_allocator_basic(clean_allocator):
    """Verifies that legacy Allocator works as expected."""
    svc = MockLegacyService()
    Allocator.res.register(svc)
    
    retrieved = Allocator.get_instance(MockLegacyService)
    assert retrieved == svc
    assert retrieved.value == "legacy"

# TDD: We want a bridge that can resolve from both.
# We'll implement it in src/core/bridge.py or similar.

def test_allocator_bridge_resolution(clean_allocator):
    """
    Verifies that the bridge can resolve from legacy Allocator.
    This test will FAIL initially until the bridge is implemented.
    """
    from src.core.bridge import LegacyAllocatorBridge
    
    svc = MockLegacyService()
    Allocator.res.register(svc)
    
    # Mock dishka container (empty)
    mock_container = MagicMock()
    mock_container.get.side_effect = Exception("Not found in Dishka")
    
    bridge = LegacyAllocatorBridge(container=mock_container)
    
    # Resolve through bridge
    retrieved = bridge.get(MockLegacyService)
    assert retrieved == svc
    assert retrieved.value == "legacy"

def test_allocator_bridge_priority(clean_allocator):
    """Verifies that Dishka takes priority over Allocator."""
    from src.core.bridge import LegacyAllocatorBridge
    
    # Register in Allocator
    legacy_svc = MockLegacyService()
    Allocator.res.register(legacy_svc)
    
    # Register in Dishka (mock)
    new_svc = MagicMock()
    new_svc.value = "new"
    
    mock_container = MagicMock()
    mock_container.get.return_value = new_svc
    
    bridge = LegacyAllocatorBridge(container=mock_container)
    
    # Resolve through bridge - should get from Dishka
    retrieved = bridge.get(MockLegacyService)
    assert retrieved == new_svc
    assert retrieved.value == "new"
    assert retrieved != legacy_svc
