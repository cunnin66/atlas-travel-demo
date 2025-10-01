from typing import List

from app.api.deps import get_current_user, get_db
from app.models.knowledge import Embedding, KnowledgeItem
from app.models.user import User
from app.schemas.knowledge import KnowledgeCreate, KnowledgeResponse, KnowledgeUpdate
from app.services.rag import process_file_for_rag, setup_vector_index, similarity_search
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    similarity_threshold: float = 0.7
    destination_id: int = None


@router.get("/", response_model=List[KnowledgeResponse])
async def get_knowledge_items(
    skip: int = 0,
    limit: int = 100,
    destination_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get knowledge base items, optionally filtered by destination"""
    query = db.query(KnowledgeItem).filter(KnowledgeItem.org_id == current_user.org_id)

    if destination_id is not None:
        query = query.filter(KnowledgeItem.destination_id == destination_id)

    knowledge_items = query.offset(skip).limit(limit).all()
    return knowledge_items


@router.post("/", response_model=KnowledgeResponse)
async def create_knowledge_item(
    knowledge_data: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge base item"""
    knowledge_item = KnowledgeItem(
        title=knowledge_data.title,
        content=knowledge_data.content,
        source_type=knowledge_data.source_type,
        source_url=knowledge_data.source_url,
        item_metadata=knowledge_data.metadata,
        tags=knowledge_data.tags,
        destination_id=knowledge_data.destination_id,
        org_id=current_user.org_id,
    )
    db.add(knowledge_item)
    db.commit()
    db.refresh(knowledge_item)
    return knowledge_item


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge_item(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific knowledge base item"""
    knowledge_item = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.id == knowledge_id,
            KnowledgeItem.org_id == current_user.org_id,
        )
        .first()
    )
    if not knowledge_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found"
        )
    return knowledge_item


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge_item(
    knowledge_id: int,
    knowledge_data: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a knowledge base item"""
    knowledge_item = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.id == knowledge_id,
            KnowledgeItem.org_id == current_user.org_id,
        )
        .first()
    )
    if not knowledge_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found"
        )

    # Update fields if provided
    update_data = knowledge_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(knowledge_item, field, value)

    db.commit()
    db.refresh(knowledge_item)
    return knowledge_item


@router.post("/upload-file")
async def upload_file_to_knowledge_base(
    file: UploadFile = File(...),
    title: str = Form(None),
    destination_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload and process a file for the knowledge base"""
    # Validate file type
    if not file.filename.lower().endswith((".pdf", ".md", ".markdown")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and Markdown files are supported",
        )

    try:
        # Read file content
        file_content = await file.read()

        # Use filename as title if not provided
        if not title:
            title = file.filename

        # Process file for RAG
        knowledge_item = process_file_for_rag(
            db=db,
            file_content=file_content,
            filename=file.filename,
            title=title,
            org_id=current_user.org_id,
            metadata={
                "original_filename": file.filename,
                "file_size": len(file_content),
            },
            destination_id=destination_id,
        )

        return {
            "message": "File processed successfully",
            "knowledge_item_id": knowledge_item.id,
            "title": knowledge_item.title,
            "chunks_created": len(knowledge_item.embeddings),
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )


@router.post("/search")
async def search_knowledge_base(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search the knowledge base using semantic similarity"""
    try:
        results = similarity_search(
            db=db,
            query=search_request.query,
            org_id=current_user.org_id,
            limit=search_request.limit,
            similarity_threshold=search_request.similarity_threshold,
            destination_id=search_request.destination_id,
        )

        return {
            "query": search_request.query,
            "results": [
                {
                    "chunk_text": result["chunk_text"],
                    "similarity": result["similarity"],
                    "knowledge_item_title": result["title"],
                    "source_type": result["source_type"],
                    "chunk_index": result["chunk_index"],
                }
                for result in results
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge base: {str(e)}",
        )


@router.post("/setup-vector-index")
async def setup_vector_index_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set up vector index for efficient similarity search (admin only)"""
    try:
        setup_vector_index(db)
        return {"message": "Vector index setup completed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up vector index: {str(e)}",
        )
