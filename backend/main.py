from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
import PyPDF2
import docx
import io
from openai import OpenAI
import faiss
import numpy as np
import time
import csv
from datetime import datetime

"""
Backend for uploading documents and extracting text.
Handles file uploads from frontend, parsing PDF, TXT, DOCX, and
preparing text for chunking.
"""
# Load values from .env
load_dotenv()

# Grabs OpenAI key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")

# Creates OpenAi client object using API key
client = OpenAI(api_key=openai_api_key)

# FAISS indexes for vector search comparison between brute force and HNSW
dimension = 1536
brute_force_index = faiss.IndexFlatIP(dimension)
hnsw_index = faiss.IndexHNSWFlat(dimension, 32)
stored_chunks = []

# Create the FastAPI app
app = FastAPI()

# Lets our frontend talk to the backend 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple check to see if backend is running
@app.get("/")
def read_root():
    return {"message": "Backend is running and cool"}

def extract_text(file_bytes: bytes, filename: str) -> str:
    # Reads file based on its type
    if filename.endswith(".pdf"):
        # Turn raw bytes into something the PDF reader can handle
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        extracted_text = ""
        # Go page by page and collect all text
        for page in pdf_reader.pages: 
            extracted_text += page.extract_text()
        return extracted_text
    elif filename.endswith(".txt"):
        # Converts raw bytes into a normal string
        return file_bytes.decode("utf-8")
    elif filename.endswith(".docx"):
        # Loads the Word doc from memory
        doc = docx.Document(io.BytesIO(file_bytes))
        extracted_text = ""
        for paragraph in doc.paragraphs:
             # Combines all paragraphs into one string
            extracted_text += paragraph.text + "\n"
        return extracted_text
    else:
         # Reject unsupported file types
        raise HTTPException(status_code=400, detail="File type is not supported")
    
def get_embeddings(chunks: list) -> list:
    """Send each chunk to OpenAI and get back a list of embeddings (numbers representing meaning)."""
    embeddings = []
    for chunk in chunks:
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def get_document_size_category(num_chunks: int) -> str:
    """Categorize document size based on estimated page count."""
    estimated_pages = num_chunks / 2
    if estimated_pages < 10:
        return "small"
    elif estimated_pages < 50:
        return "medium"
    elif estimated_pages < 200:
        return "large"
    else:
        return "very_large"
    
def log_comparison(bf_time: float, hnsw_time: float, bf_indices: list, hnsw_indices: list, doc_size: str):
    """Logs brute force vs HNSW comparison results to a CSV file for analysis."""
    log_file = "algorithms_comparison.csv"
    file_exists = os.path.isfile(log_file)

    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "doc_size", "bf_time_ms", "hnsw_time_ms", "bf_indices", "hnsw_indices"])
        writer.writerow([
            datetime.now().isoformat(),
            doc_size,
            round(bf_time, 4),
            round(hnsw_time, 4),
            bf_indices,
            hnsw_indices
        ])

def search_both_indexes(query_embedding: list, k: int = 5) -> dict:
    """Run both HNSW and brute force search, logs comparison results, returns brute force chunks."""
    # Converts qusetion embedding to numpy format so FAISS can read it
    query_vector = np.array([query_embedding]).astype("float32")
    faiss.normalize_L2(query_vector)

    # Brute force search
    start = time.time()
    _, bf_indices = brute_force_index.search(query_vector, k)
    bf_time = (time.time() - start) * 1000

    # HNSW search
    start = time.time()
    _, hnsw_indices = hnsw_index.search(query_vector, k)
    hnsw_time = (time.time() - start) * 1000

    doc_size = get_document_size_category(len(stored_chunks))

    log_comparison(bf_time, hnsw_time, bf_indices[0].tolist(), hnsw_indices[0].tolist(), doc_size)

    return [stored_chunks[i] for i in bf_indices[0] if i < len(stored_chunks)]
    
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
     # Breaks text into words first
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        # Builds a chunk from a slice of words
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
         # Moves start forward but keep some overlap so context isn't lost
        start = end - overlap

    return chunks
    
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read uploaded file into memory and extract text from it 
    file_bytes = await file.read()
    extracted_text = extract_text(file_bytes, file.filename)
    return {"message": "File uploaded successfully", "characters": len(text)}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accepts a document, extracts text, chunks it, embeds it, and stores in both FAISS indexes."""
    global stored_chunks
    
    # Reads file and final output are embeddings
    file_bytes = await file.read()
    extracted_text = extract_text(file_bytes, file.filename)
    chunks = chunk_text(extracted_text)
    embeddings = get_embeddings(chunks)
    
    # Converts list to numpy array so that FAISS can read it
    vectors = np.array(embeddings).astype("float32")
    faiss.normalize_L2(vectors)
    
    # Adds vectors to both indexes
    brute_force_index.add(vectors)
    hnsw_index.add(vectors)
    stored_chunks = chunks
    
    return {"message": "File uploaded successfully", "chunks": len(chunks)}