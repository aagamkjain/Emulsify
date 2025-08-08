import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
# import easyocr  # Removed for simplicity - using pypdf text extraction instead
import weaviate
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile

# Load environment variables
load_dotenv()

# Configure Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# OCR initialization removed - using pypdf text extraction instead

# Initialize Weaviate client for local Docker instance using v4 API
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051,
    skip_init_checks=True
)

# Create Weaviate schema if it doesn't exist

try:
    client.collections.create(
        name="Document",
        vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_transformers(),
        properties=[
            weaviate.classes.config.Property(name="content", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="category", data_type=weaviate.classes.config.DataType.TEXT),
        ]
    )
except Exception as e:
    if "already exists" in str(e).lower():
        print("Schema already exists")
    else:
        print(f"Schema creation error: {e}")

def process_pdf(file):
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file.getvalue())
        temp_path = temp_file.name

    # Extract text from PDF
    text = ""
    pdf = PdfReader(temp_path)
    
    for page_num, page in enumerate(pdf.pages):
        # For now, we'll extract text directly from PDF using pypdf
        # Note: For proper OCR from PDF pages, you'd need to convert PDF to images first
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "
    
    # Clean up temporary file
    os.unlink(temp_path)
    
    return text

def chunk_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def categorize_chunks_batch(chunks):
    """Categorize multiple chunks in a single Gemini request"""
    if not chunks:
        return []
    
    # Create a batch prompt with all chunks
    prompt = "Categorize each of the following text chunks into a single word category. Return only the categories, one per line, in the same order as the chunks:\n\n"
    
    for i, chunk in enumerate(chunks, 1):
        prompt += f"Chunk {i}:\n{chunk[:500]}...\n\n"  # Limit chunk length to avoid token limits
    
    prompt += "Categories (one per line):"
    
    try:
        response = model.generate_content(prompt)
        categories = response.text.strip().split('\n')
        
        # Clean up categories and ensure we have the right number
        categories = [cat.strip() for cat in categories if cat.strip()]
        
        # If we don't get the right number of categories, fall back to default
        if len(categories) != len(chunks):
            print(f"Warning: Expected {len(chunks)} categories, got {len(categories)}. Using default category.")
            categories = ["document"] * len(chunks)
        
        return categories
    except Exception as e:
        print(f"Error categorizing chunks: {e}")
        return ["document"] * len(chunks)  # Default fallback

def store_in_weaviate(chunks):
    # Batch categorize all chunks at once
    categories = categorize_chunks_batch(chunks)
    
    # Store all chunks with their categories using v4 API
    document_collection = client.collections.get("Document")
    for chunk, category in zip(chunks, categories):
        document_collection.data.insert({
            "content": chunk,
            "category": category
        })

def search_weaviate(query):
    # Use Gemini to enhance the search query
    prompt = f"Enhance this search query for better semantic search results: {query}"
    enhanced_query = model.generate_content(prompt).text
    
    # Search Weaviate using v4 API
    document_collection = client.collections.get("Document")
    response = document_collection.query.bm25(
        query=enhanced_query,
        query_properties=["content", "category"],
        limit=3
    )
    
    return response.objects

# Streamlit UI
st.title("PDF Document Search Engine")

# File upload
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded_file is not None:
    if st.button("Process PDF"):
        with st.spinner("Processing PDF..."):
            # Extract text from PDF
            text = process_pdf(uploaded_file)
            
            # Chunk the text
            chunks = chunk_text(text)
            
            # Store in Weaviate
            store_in_weaviate(chunks)
            
            st.success("PDF processed and stored successfully!")

# Search interface
search_query = st.text_input("Enter your search query")
if search_query:
    if st.button("Search"):
        with st.spinner("Searching..."):
            results = search_weaviate(search_query)
            
            for result in results:
                st.write("---")
                st.write("**Category:**", result.properties.get("category", "Unknown"))
                st.write("**Content:**", result.properties.get("content", "No content"))
