from typing import List
from pydantic import Field
from src.core.messages import Command, Event
from .domain.interfaces import SearchResult

class SearchImagesCommand(Command):
    query: str
    limit: int = 10

class SearchResultsEvent(Event):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
