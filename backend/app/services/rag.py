import io
import re
from typing import List, Tuple

import markdown
import PyPDF2
import tiktoken
from app.core.config import settings
from app.models.knowledge import Embedding, KnowledgeItem
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize tokenizer for accurate token counting
encoding = tiktoken.get_encoding("cl100k_base")  # Used by text-embedding-ada-002


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from PDF or Markdown files"""
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_content)
    elif filename.lower().endswith((".md", ".markdown")):
        return extract_text_from_markdown(file_content)
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content"""
    pdf_file = io.BytesIO(file_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_markdown(file_content: bytes) -> str:
    """Extract text from Markdown file content"""
    md_text = file_content.decode("utf-8")
    # Convert markdown to plain text (removes formatting)
    html = markdown.markdown(md_text)
    # Simple HTML tag removal
    text = re.sub("<[^<]+?>", "", html)
    return text.strip()


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    return len(encoding.encode(text))


def create_chunks_with_overlap(
    text: str, min_tokens: int = 800, max_tokens: int = 1200, overlap_tokens: int = 40
) -> List[Tuple[str, int]]:
    """
    Create text chunks with specified token limits and overlap.
    Returns list of tuples (chunk_text, token_count)
    """
    # Split text into sentences and paragraphs for better chunking
    sentences = re.split(r"(?<=[.!?])\s+|\n\s*\n", text)

    chunks = []
    current_chunk = ""
    current_tokens = 0

    i = 0
    while i < len(sentences):
        sentence = sentences[i].strip()
        if not sentence:
            i += 1
            continue

        sentence_tokens = count_tokens(sentence)

        # If adding this sentence would exceed max_tokens, finalize current chunk
        if current_tokens + sentence_tokens > max_tokens and current_chunk:
            chunks.append((current_chunk.strip(), current_tokens))

            # Create overlap by including recent sentences
            overlap_text = ""
            overlap_token_count = 0
            j = i - 1

            # Go backwards to build overlap
            while j >= 0 and overlap_token_count < overlap_tokens:
                prev_sentence = sentences[j].strip()
                if prev_sentence:
                    prev_tokens = count_tokens(prev_sentence)
                    if (
                        overlap_token_count + prev_tokens <= overlap_tokens * 2
                    ):  # Allow some flexibility
                        overlap_text = prev_sentence + " " + overlap_text
                        overlap_token_count += prev_tokens
                j -= 1

            current_chunk = overlap_text
            current_tokens = overlap_token_count

        # Add current sentence to chunk
        if current_chunk:
            current_chunk += " " + sentence
        else:
            current_chunk = sentence
        current_tokens += sentence_tokens

        # If chunk is at minimum size and we have a natural break, consider finalizing
        if current_tokens >= min_tokens:
            # Look ahead to see if there's a natural break
            if i + 1 < len(sentences):
                next_sentence = sentences[i + 1].strip()
                if not next_sentence or next_sentence.startswith(("\n", "#")):
                    chunks.append((current_chunk.strip(), current_tokens))
                    current_chunk = ""
                    current_tokens = 0

        i += 1

    # Add remaining text as final chunk
    if current_chunk.strip():
        chunks.append((current_chunk.strip(), current_tokens))

    return chunks


def generate_embeddings(text: str) -> List[float]:
    """Generate embeddings using OpenAI's text-embedding-ada-002"""
    try:
        response = client.embeddings.create(model="text-embedding-ada-002", input=text)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise


def store_knowledge_item_with_embeddings(
    db: Session,
    title: str,
    content: str,
    source_type: str,
    org_id: int,
    chunks: List[Tuple[str, int]],
    embeddings: List[List[float]],
    metadata: dict = None,
    destination_id: int = None,
) -> KnowledgeItem:
    """Store knowledge item and its embeddings in the database"""

    # Create knowledge item
    knowledge_item = KnowledgeItem(
        title=title,
        content=content,
        source_type=source_type,
        org_id=org_id,
        destination_id=destination_id,
        item_metadata=metadata or {},
    )
    db.add(knowledge_item)
    db.flush()  # Get the ID

    # Create embeddings
    for i, ((chunk_text, token_count), embedding) in enumerate(zip(chunks, embeddings)):
        embedding_obj = Embedding(
            knowledge_item_id=knowledge_item.id,
            chunk_text=chunk_text,
            embedding_vector=embedding,
            chunk_index=i,
            token_count=token_count,
        )
        db.add(embedding_obj)

    db.commit()
    return knowledge_item


def process_file_for_rag(
    db: Session,
    file_content: bytes,
    filename: str,
    title: str,
    org_id: int,
    metadata: dict = None,
    destination_id: int = None,
) -> KnowledgeItem:
    """Complete pipeline to process a file for RAG"""

    # Extract text
    text = extract_text_from_file(file_content, filename)

    # Create chunks
    chunks = create_chunks_with_overlap(text)

    # Generate embeddings for each chunk
    embeddings = []
    for chunk_text, _ in chunks:
        embedding = generate_embeddings(chunk_text)
        embeddings.append(embedding)

    # Store in database
    source_type = "pdf" if filename.lower().endswith(".pdf") else "markdown"
    knowledge_item = store_knowledge_item_with_embeddings(
        db=db,
        title=title,
        content=text,
        source_type=source_type,
        org_id=org_id,
        chunks=chunks,
        embeddings=embeddings,
        metadata=metadata,
        destination_id=destination_id,
    )

    return knowledge_item


def setup_vector_index(db: Session):
    """Set up vector index for efficient similarity search"""
    try:
        # Create the pgvector extension if it doesn't exist
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create an index on the embedding_vector column for faster similarity search
        db.execute(
            text(
                """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS embeddings_vector_idx
            ON embeddings USING ivfflat (embedding_vector vector_cosine_ops)
            WITH (lists = 100)
        """
            )
        )

        db.commit()
        print("Vector index created successfully")
    except Exception as e:
        print(f"Error setting up vector index: {e}")
        db.rollback()


def similarity_search(
    db: Session,
    query: str,
    org_id: int,
    limit: int = 5,
    similarity_threshold: float = 0.7,
    destination_id: int = None,
) -> List[dict]:
    """Perform similarity search on embeddings"""

    # Generate embedding for query
    query_embedding = generate_embeddings(query)

    # Perform similarity search
    destination_filter = ""
    if destination_id is not None:
        destination_filter = "AND k.destination_id = :destination_id"

    query_sql = text(
        f"""
        SELECT e.chunk_text, e.chunk_index, e.token_count,
               k.title, k.source_type,
               1 - (e.embedding_vector <=> :query_embedding) as similarity
        FROM embeddings e
        JOIN knowledge_items k ON e.knowledge_item_id = k.id
        WHERE k.org_id = :org_id
          AND 1 - (e.embedding_vector <=> :query_embedding) > :threshold
          {destination_filter}
        ORDER BY e.embedding_vector <=> :query_embedding
        LIMIT :limit
    """
    )

    params = {
        "query_embedding": str(query_embedding),
        "org_id": org_id,
        "threshold": similarity_threshold,
        "limit": limit,
    }

    if destination_id is not None:
        params["destination_id"] = destination_id

    result = db.execute(query_sql, params)

    # Convert to list of dictionaries
    results = []
    for row in result.fetchall():
        results.append(
            {
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "token_count": row.token_count,
                "title": row.title,
                "source_type": row.source_type,
                "similarity": float(row.similarity),
            }
        )

    return results
