from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import PyPDF2
from llm_agent import config

def load_pdf_content(file_path):
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n\n".join(clean_page(page.extract_text() or "") for page in reader.pages)
    return text

def clean_page(text):
    text = re.sub(r"\s{2,}", " ", text)  # normalize spaces
    text = re.sub(r"\n{2,}", "\n\n", text)  # normalize paragraphs
    return text.strip()

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)
