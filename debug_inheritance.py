import sys
from pathlib import Path

# Fix path
root = Path(__file__).resolve().parent
sys.path.append(str(root))

try:
    from bubus import BaseEvent
    print("--- sys.path ---")
    for p in sys.path:
        print(f"  {p}")
    print("----------------")
    
    import bubus
    print(f"Bubus location: {bubus.__file__}")
    import src.core.messages
    print(f"src.core.messages location: {src.core.messages.__file__}")
    
    from bubus import BaseEvent as BE1
    from bubus.models import BaseEvent as BE2
    print(f"BE from bubus: {id(BE1)} (Mod: {BE1.__module__})")
    print(f"BE from bubus.models: {id(BE2)} (Mod: {BE2.__module__})")
    print(f"Match? {BE1 is BE2}")
    
    from src.core.messages import Message
    print(f"Message base check: {id(Message.__bases__[0])}")
    print(f"Message base matches BE from bubus? {Message.__bases__[0] is BE1}")
    
    from src.apps.experemental.boruscraper.module import BoruScraperModule
    
    module = BoruScraperModule()
    print(f"Module Command Handlers: {module.command_handlers.keys()}")
    
    for cmd_type in module.command_handlers.keys():
        print(f"Checking {cmd_type}:")
        print(f"  MRO: {cmd_type.__mro__}")
        print(f"  Is subclass of BaseEvent? {issubclass(cmd_type, BaseEvent)}")
        if not issubclass(cmd_type, BaseEvent):
            print(f"  FAILED! Expected BaseEvent: {BaseEvent}")
            print(f"  Actual BaseEvent in MRO: {[b for b in cmd_type.__mro__ if 'BaseEvent' in str(b)]}")
            if hasattr(cmd_type, "model_fields"):
                 print(f"  Pydantic check: {cmd_type.model_fields.keys()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
