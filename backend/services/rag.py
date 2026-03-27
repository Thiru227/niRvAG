"""
RAG System — ChromaDB document retrieval with optimized chunking
"""
import os
import re

try:
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chroma_store')
    os.makedirs(CHROMA_PATH, exist_ok=True)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    collection = chroma_client.get_or_create_collection(
        name="support_docs",
        embedding_function=embedding_fn
    )
    CHROMA_AVAILABLE = True
    print(f"✅ ChromaDB initialized at {CHROMA_PATH} — {collection.count()} docs indexed")
except Exception as e:
    print(f"⚠️ ChromaDB not available: {e}")
    CHROMA_AVAILABLE = False
    collection = None


def index_document(text: str, doc_id: str, filename: str) -> int:
    """Chunk → embed → store in ChromaDB. Returns chunk count."""
    if not CHROMA_AVAILABLE or not collection:
        print("ChromaDB not available, skipping indexing")
        return 0

    # Delete existing chunks for this document (re-index support)
    delete_document(doc_id)

    chunks = chunk_text(text, chunk_size=500, overlap=100)

    if not chunks:
        print(f"No chunks generated from document: {filename}")
        return 0

    # ChromaDB has a batch limit, so add in batches of 40
    batch_size = 40
    total_added = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids = [f"{doc_id}_chunk_{j}" for j in range(i, i + len(batch))]
        metadatas = [{"filename": filename, "chunk_index": j, "doc_id": doc_id} for j in range(i, i + len(batch))]

        collection.add(
            documents=batch,
            ids=ids,
            metadatas=metadatas
        )
        total_added += len(batch)

    print(f"✅ Indexed {total_added} chunks for '{filename}' (doc_id: {doc_id})")
    return total_added


def delete_document(doc_id: str):
    """Remove all chunks belonging to a document (for re-indexing)."""
    if not CHROMA_AVAILABLE or not collection:
        return
    try:
        # Get all IDs that start with this doc_id
        existing = collection.get(where={"doc_id": doc_id})
        if existing and existing['ids']:
            collection.delete(ids=existing['ids'])
            print(f"🗑️ Deleted {len(existing['ids'])} old chunks for doc {doc_id}")
    except Exception as e:
        # Fallback: try prefix-based deletion
        try:
            all_data = collection.get()
            to_delete = [id for id in all_data['ids'] if id.startswith(f"{doc_id}_")]
            if to_delete:
                collection.delete(ids=to_delete)
                print(f"🗑️ Deleted {len(to_delete)} old chunks for doc {doc_id}")
        except Exception as e2:
            print(f"Could not delete old chunks: {e2}")

# Alias for external use
delete_document_chunks = delete_document


def retrieve_context(query: str, top_k: int = 5) -> str:
    """Semantic search → return relevant context string."""
    if not CHROMA_AVAILABLE or not collection:
        return "No relevant documentation found."

    try:
        count = collection.count()
        if count == 0:
            return "No documents have been indexed yet."

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, count)
        )

        if not results['documents'] or not results['documents'][0]:
            return "No relevant documentation found."

        # Include source filename for attribution
        context_parts = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i] if results['metadatas'] else {}
            source = meta.get('filename', 'unknown')
            context_parts.append(f"[Source: {source}]\n{doc}")

        return "\n\n---\n".join(context_parts)
    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return "No relevant documentation found."


def get_collection_stats() -> dict:
    """Get stats about the ChromaDB collection."""
    if not CHROMA_AVAILABLE or not collection:
        return {"available": False, "count": 0}
    try:
        return {"available": True, "count": collection.count()}
    except Exception:
        return {"available": True, "count": 0}


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list:
    """
    Split text into overlapping chunks using sentence-aware splitting.
    
    Strategy:
    1. Split text into sentences
    2. Group sentences into chunks of ~chunk_size words
    3. Overlap chunks by ~overlap words for context continuity
    """
    if not text or not text.strip():
        return []

    # Clean the text
    text = text.strip()
    text = re.sub(r'\n{3,}', '\n\n', text)  # Collapse excessive newlines
    text = re.sub(r' {2,}', ' ', text)       # Collapse multiple spaces

    # Split into sentences (handles . ! ? and newline boundaries)
    sentences = re.split(r'(?<=[.!?])\s+|\n{2,}', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    chunks = []
    current_chunk_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())

        # If a single sentence exceeds chunk_size, split it by words
        if sentence_words > chunk_size:
            # Flush current chunk first
            if current_chunk_sentences:
                chunks.append(' '.join(current_chunk_sentences))

            words = sentence.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk = ' '.join(words[i:i + chunk_size])
                if chunk.strip():
                    chunks.append(chunk)

            current_chunk_sentences = []
            current_word_count = 0
            continue

        # If adding this sentence would exceed chunk_size, finalize current chunk
        if current_word_count + sentence_words > chunk_size and current_chunk_sentences:
            chunks.append(' '.join(current_chunk_sentences))

            # Keep overlap: take sentences from the end of current chunk
            overlap_sentences = []
            overlap_word_count = 0
            for s in reversed(current_chunk_sentences):
                s_words = len(s.split())
                if overlap_word_count + s_words > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_word_count += s_words

            current_chunk_sentences = overlap_sentences
            current_word_count = overlap_word_count

        current_chunk_sentences.append(sentence)
        current_word_count += sentence_words

    # Don't forget the last chunk
    if current_chunk_sentences:
        chunks.append(' '.join(current_chunk_sentences))

    # Filter out tiny chunks (less than 10 words)
    chunks = [c for c in chunks if len(c.split()) >= 10]

    return chunks
