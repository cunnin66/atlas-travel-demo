from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    """Base knowledge schema"""
    title: str
    content: str
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []


class KnowledgeCreate(KnowledgeBase):
    """Knowledge creation schema"""
    pass


class KnowledgeUpdate(BaseModel):
    """Knowledge update schema"""
    title: Optional[str] = None
    content: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class KnowledgeResponse(KnowledgeBase):
    """Knowledge response schema"""
    id: int
    org_id: int
    
    class Config:
        from_attributes = True
