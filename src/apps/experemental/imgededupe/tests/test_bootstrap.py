import sys
import os
import pytest
from src.core.system import System

@pytest.mark.asyncio
async def test_imgededupe_module_bootstrap():
    """
    Test that the ImgeDedupeModule can be bootstrapped by the BCor System.
    """
    # 1. Import module absolutely
    from src.apps.experemental.imgededupe.module import ImgeDeduplicationModule
    
    module = ImgeDeduplicationModule()
    system = System(modules=[module])
    
    # 2. Bootstrap (this usually requires app.toml to be present and valid)
    await system.start()
    
    # 4. Verify system is running and module is registered
    # 4. Verify system is running
    assert system._initialized
    assert module.name == "imgededupe"
    
    # 5. Cleanup
    await system.stop()
