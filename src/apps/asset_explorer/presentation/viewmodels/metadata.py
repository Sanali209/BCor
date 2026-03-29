from enum import Enum
from dataclasses import dataclass, field
from typing import Any, List, Optional, Type, get_type_hints, Union, get_args, get_origin
from PySide6.QtCore import QObject, Signal, Slot
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.metadata import get_field_metadata, Stored, Rel
from src.modules.agm.ui_metadata import DisplayName, Hidden

class PropertyCategory(str, Enum):
    """Categorization of a property for UI rendering."""
    TEXT = "TEXT"
    LONG_TEXT = "LONG_TEXT"
    URL = "URL"
    NUMBER = "NUMBER"
    DATE = "DATE"
    TAGS = "TAGS"
    BOOLEAN = "BOOLEAN"
    READ_ONLY = "READ_ONLY"

@dataclass
class PropertyDescriptor:
    """Descriptor describing how a property should be rendered in the Auto-GUI."""
    id: str
    name: str # The technical ID
    display_name: str
    value: Any
    category: PropertyCategory = PropertyCategory.TEXT
    is_stored: bool = False
    is_relation: bool = False
    handler: Optional[str] = None
    rel_type: Optional[str] = None
    data_type: Type = Any

class MetadataViewModel(QObject):
    """
    ViewModel handling dynamic metadata introspection for an Asset.
    Acts as the 'brain' for the Auto-GUI Right Panel.
    """
    property_changed = Signal(str, object) # field_name, new_value
    save_started = Signal()
    save_finished = Signal(bool)

    def __init__(self, asset: Any, mapper: Optional[AGMMapper] = None, parent=None):
        super().__init__(parent)
        self._asset = asset
        self._mapper = mapper
        self._descriptors = self._introspect()

    @property
    def descriptors(self) -> List[PropertyDescriptor]:
        return self._descriptors

    def _introspect(self) -> List[PropertyDescriptor]:
        descriptors = []
        cls = self._asset.__class__
        hints = get_type_hints(cls, include_extras=True)
        
        for field_name, hint in hints.items():
            metadata = get_field_metadata(cls, field_name)
            
            # 1. Check for Hidden
            if any(isinstance(m, Hidden) for m in metadata):
                continue
            
            # 2. Extract DisplayName
            display_name = field_name
            for m in metadata:
                if isinstance(m, DisplayName):
                    display_name = m.name
            
            # 3. Detect Stored/Rel
            is_stored = False
            handler = None
            for m in metadata:
                if isinstance(m, Stored):
                    is_stored = True
                    handler = m.handler
            
            is_rel = False
            rel_type = None
            for m in metadata:
                if isinstance(m, Rel):
                    is_rel = True
                    rel_type = m.type
            
            val = getattr(self._asset, field_name, None)
            
            # 4. Infer Category
            category = self._infer_category(field_name, hint, is_stored, is_rel, rel_type)
            
            descriptors.append(PropertyDescriptor(
                id=field_name,
                name=field_name,
                display_name=display_name,
                value=val,
                category=category,
                is_stored=is_stored,
                is_relation=is_rel,
                handler=handler,
                rel_type=rel_type,
                data_type=hint
            ))
            
        return descriptors

    def _infer_category(self, field_name: str, hint: Any, is_stored: bool, is_rel: bool, rel_type: str | None) -> PropertyCategory:
        """Infer the best UI category for a given field."""
        
        # Unpack Annotated if present
        origin = get_origin(hint)
        if origin is Union:
            args = get_args(hint)
            # Find the primary type (non-None)
            primary = next((a for a in args if a is not type(None)), Any)
            hint = primary

        # READ_ONLY triggers
        if field_name == "id" or is_stored:
            return PropertyCategory.READ_ONLY

        # URL detection
        if field_name == "uri" or "url" in field_name.lower():
            return PropertyCategory.URL
        
        # Boolean
        if hint is bool:
            return PropertyCategory.BOOLEAN

        # Numeric (int/float)
        if hint in (int, float):
            return PropertyCategory.NUMBER
        
        # DateTime heuristics
        if "at" in field_name.lower() or "date" in field_name.lower() or "time" in field_name.lower():
            if hint in (float, int): # Unix timestamp
                return PropertyCategory.DATE

        # Tags / Relationships
        if is_rel:
            if rel_type in ("HAS_TAG", "HAS_WD_TAG", "CHILD_OF"):
                return PropertyCategory.TAGS
            return PropertyCategory.READ_ONLY # Default for complex links for now

        # Long text heuristic
        if field_name in ("description", "prompt", "content"):
            return PropertyCategory.LONG_TEXT

        return PropertyCategory.TEXT

    @Slot(str, object)
    def update_property(self, field_name: str, value: Any):
        """Update a property in the underlying asset."""
        if hasattr(self._asset, field_name):
            setattr(self._asset, field_name, value)
            # Find and update the descriptor in memory
            for desc in self._descriptors:
                if desc.id == field_name:
                    desc.value = value
                    break
            self.property_changed.emit(field_name, value)

    async def save_changes(self):
        """Persist changes to the underlying storage (Neo4j and/or local EXIF)."""
        if not self._mapper:
            return
        
        self.save_started.emit()
        try:
            # 1. Persist to Graph via AGMMapper (Atomic)
            await self._mapper.save(self._asset)
            
            # 2. Local File Update (EXIF/XMP) - Phase 3
            # Sync core fields (Title, Description, Tags) back to file headers for local files
            uri = getattr(self._asset, "uri", "")
            if uri and str(uri).startswith("file://"):
                from src.modules.assets.infrastructure.handlers.pyexiv2 import Pyexiv2Handler
                
                tags_to_sync = {}
                
                # Map Asset model fields to standard XMP tags
                if hasattr(self._asset, "name") and self._asset.name:
                    tags_to_sync["Xmp.dc.title"] = self._asset.name
                
                if hasattr(self._asset, "description") and self._asset.description:
                    tags_to_sync["Xmp.dc.description"] = self._asset.description
                
                if hasattr(self._asset, "tags") and self._asset.tags:
                    # tags is a list of Tag objects. DC:subject expects a list/comma string.
                    tag_names = [t.name if hasattr(t, "name") else str(t) for t in self._asset.tags]
                    if tag_names:
                        tags_to_sync["Xmp.dc.subject"] = ", ".join(tag_names)
                
                if tags_to_sync:
                    from loguru import logger
                    logger.info(f"MetadataViewModel: Syncing changes to {uri}: {tags_to_sync}")
                    success = await Pyexiv2Handler.write_xmp(uri, tags_to_sync)
                    if not success:
                        logger.warning(f"MetadataViewModel: Partial failure - Graph saved, but File write-back failed for {uri}")
            
            self.save_finished.emit(True)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to save metadata for {self._asset.id}: {e}")
            self.save_finished.emit(False)
