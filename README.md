# PDF OCR RAG Pipeline

This project implements a Retrieval Augmented Generation (RAG) pipeline using PaddleOCR for PDF text extraction, Langchain for text chunking, Google's Gemini Pro for text understanding, and Weaviate as the vector database.

## Features

- PDF text extraction using PaddleOCR
- Text chunking using Langchain's RecursiveCharacterTextSplitter
- Semantic categorization using Google's Gemini Pro
- Vector storage and search using Weaviate
- React frontend with flaskAPI backend

## Setup

1. Create a `.env` file with the following variables:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   WEAVIATE_URL=your_weaviate_instance_url
   WEAVIATE_API_KEY=your_weaviate_api_key
   ```

2. Install the required packages:
   ```
   pip install paddleocr langchain google-generativeai weaviate-client python-dotenv PyPDF2 streamlit
   ```

3. Install docker:
   Connect weaviate to docker, to run the database locally
   

5. Run the application:
   ```
   FRONTEND:
   cd frontend
   npm start

   BACKEND:
   python backend.py
   ```

## Usage

1. Upload a PDF document using the file uploader
2. Click "Process PDF" to extract text and store it in the database
3. Enter search queries in the search box to retrieve relevant information

## How it Works

1. The PDF is processed using PaddleOCR to extract text
2. The extracted text is split into chunks using Langchain's RecursiveCharacterTextSplitter
3. Each chunk is categorized using Gemini Pro
4. Chunks are stored in Weaviate along with their categories
5. Search queries are enhanced using Gemini Pro for better semantic matching
6. Results are retrieved from Weaviate based on semantic similarity




