import uuid
from llm_agent.utils.embedding import EmbeddingModel
from llm_agent.utils.vectorstore import VectorStore
from llm_agent.tools.pdf_loader import load_pdf_content, chunk_text

def ingest_pdf_from_path(file_path, collection_name: str):
    text = load_pdf_content(file_path)
    return ingest_text(text, collection_name)

def ingest_text(text: str, collection_name: str):
    if not text.strip():
        raise ValueError("No text to ingest.")

    chunks = chunk_text(text)
    chunks = list(dict.fromkeys(chunks))  # Deduplicate identical chunks

    embedder = EmbeddingModel()
    embeddings = embedder.embed_texts(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]

    vectorstore = VectorStore(collection_name=collection_name)
    vectorstore.add_documents(ids=ids, texts=chunks, embeddings=embeddings)

    return len(chunks)
