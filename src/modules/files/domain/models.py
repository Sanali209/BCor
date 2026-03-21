from datetime import datetime
from typing import List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

class AIExpertiseModel(BaseModel):
    service_name: str
    backend_name: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FileModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default=None)
    local_path: str
    name: str
    ext: Optional[str] = None
    size: Optional[int] = None
    md5: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Compatibility and tracking
    source: Optional[str] = None
    indexed_by: List[str] = Field(default_factory=list)
    rating: int = 0
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_deleted: bool = False
    
    # AI data
    ai_expertise: List[AIExpertiseModel] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
