from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ============================================================
# Build RAG Vector Database
# ============================================================

load_dotenv()

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
CHROMA_DB_DIR = "chroma_db"


def load_documents():
    documents = []

    if not KNOWLEDGE_BASE_DIR.exists():
        raise FileNotFoundError(
            "knowledge_base folder not found. Create it and add .txt files."
        )

    text_files = list(KNOWLEDGE_BASE_DIR.glob("*.txt"))

    if not text_files:
        raise FileNotFoundError(
            "No .txt files found in knowledge_base folder."
        )

    for file_path in text_files:
        loader = TextLoader(str(file_path), encoding="utf-8")
        documents.extend(loader.load())

    return documents


def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    return text_splitter.split_documents(documents)


def build_vector_database(docs):
    embedding_model = OpenAIEmbeddings()

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory=CHROMA_DB_DIR
    )

    return vectorstore


def main():
    documents = load_documents()
    docs = split_documents(documents)
    build_vector_database(docs)

    print("RAG knowledge base built successfully.")
    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks created: {len(docs)}")
    print(f"Vector database folder: {CHROMA_DB_DIR}")


if __name__ == "__main__":
    main()
