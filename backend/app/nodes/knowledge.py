from typing import Any, Dict, List

from app.database import SessionLocal
from app.nodes.base import BaseTool
from app.services.rag import similarity_search
from pydantic import BaseModel, Field


class KnowledgeSearchSchema(BaseModel):
    """Schema for knowledge search parameters"""

    query: str = Field(description="Query to search the knowledge base")


class KnowledgeResult(BaseModel):
    """Schema for a single knowledge search result"""

    chunk_text: str = Field(description="The relevant text chunk")
    title: str = Field(description="Title of the knowledge item")
    source_type: str = Field(description="Type of source (pdf, markdown, etc.)")
    similarity: float = Field(description="Similarity score (0-1)")
    chunk_index: int = Field(description="Index of the chunk within the document")
    token_count: int = Field(description="Number of tokens in the chunk")


class KnowledgeResultSchema(BaseModel):
    """Schema for knowledge search result"""

    results: List[KnowledgeResult]
    query: str = Field(description="The original search query")
    total_results: int = Field(description="Total number of results found")


class KnowledgeRagTool(BaseTool):
    """Tool for searching knowledge base using RAG"""

    name: str = "knowledge_base"
    description: str = "Search for real knowledge base using RAG. Provides actual knowledge base data with pricing and schedules."

    def get_args_schema(self) -> BaseModel:
        return KnowledgeSearchSchema

    def get_result_schema(self) -> BaseModel:
        return KnowledgeResultSchema

    async def execute(
        self,
        query: str,
        org_id: int = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Execute knowledge search using RAG"""
        try:
            # Create database session
            db = SessionLocal()

            try:
                # If org_id is not provided, we'll need to get it from context
                # For now, we'll use a default or raise an error
                if org_id is None:
                    # In a real implementation, this would come from the user context
                    # For now, we'll search across all orgs (remove org filter)
                    # This is not ideal for production but works for the demo
                    results = []
                    # We need to modify the similarity_search to handle no org_id
                    # For now, let's use org_id = 1 as a fallback
                    org_id = 1

                # Perform similarity search using the RAG service
                search_results = similarity_search(
                    db=db,
                    query=query,
                    org_id=org_id,
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                    destination_id=None,  # As requested, destination_id doesn't matter
                )

                # Convert results to our schema format
                knowledge_results = []
                for result in search_results:
                    knowledge_result = KnowledgeResult(
                        chunk_text=result["chunk_text"],
                        title=result["title"],
                        source_type=result["source_type"],
                        similarity=result["similarity"],
                        chunk_index=result["chunk_index"],
                        token_count=result["token_count"],
                    )
                    knowledge_results.append(knowledge_result)

                # Create response
                response = KnowledgeResultSchema(
                    results=knowledge_results,
                    query=query,
                    total_results=len(knowledge_results),
                )

                return {
                    "success": True,
                    "data": response.dict(),
                    "message": f"Found {len(knowledge_results)} relevant knowledge items",
                }

            finally:
                db.close()

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search knowledge base: {str(e)}",
            }


knowledge_rag_tool = KnowledgeRagTool()
