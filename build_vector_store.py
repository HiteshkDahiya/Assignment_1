import asyncio
import re
from pathlib import Path
from pypdf import PdfReader

from autogen_ext.memory.chromadb import (
    ChromaDBVectorMemory,
    PersistentChromaDBVectorMemoryConfig,
    SentenceTransformerEmbeddingFunctionConfig,
)
from autogen_core.memory import MemoryContent, MemoryMimeType

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = BASE_DIR / "vector_store"

PDF_PATHS = [
    "docs/Automated Expense.pdf",
    "docs/Chemist Bot.pdf",
    "docs/DCR.pdf",
    "docs/General Bot.pdf",
    "docs/Goal Bot.pdf",
    "docs/HR Bot.pdf",
    "docs/LMS bot.pdf",
    "docs/Prescription Bot.pdf",
    "docs/Voice Command.pdf",
]

def load_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = " ".join(
        page.extract_text() or "" for page in reader.pages
    )
    text = text.replace("\x00", "")
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str, chunk_size=400, overlap=80):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

async def build_vector_store():
    vm = ChromaDBVectorMemory(
        config=PersistentChromaDBVectorMemoryConfig(
            collection_name="pdf_docs",
            persist_directory=str(PERSIST_DIR),
            similarity_top_k=12,
            embedding_function_config=SentenceTransformerEmbeddingFunctionConfig(
                model_name="all-mpnet-base-v2"
            ),
        )
    )

    for path in PDF_PATHS:
        text = load_pdf_text(path)
        for chunk in chunk_text(text):
            await vm.add(
                MemoryContent(
                    content=chunk,
                    mime_type=MemoryMimeType.TEXT,
                    metadata={"source": path},
                )
            )

    print("Vector store created successfully")

if __name__ == "__main__":
    asyncio.run(build_vector_store())
