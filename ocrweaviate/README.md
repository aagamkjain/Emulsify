# 🏛️ PDF Policy Query System

**Production-ready system for querying policy documents using OCR + Weaviate + Gemini 2.5 Pro**

Transform complex policy documents into simple, understandable answers for everyday users.

## ✨ Features

- **🔍 Intelligent OCR**: Extracts text from PDFs with automatic fallback to OCR for image-based documents
- **🧹 Text Cleaning**: Removes duplicates, reorders lines, and normalizes messy OCR output
- **🎯 Single Best Answer**: Returns only the most relevant result, not multiple confusing options
- **👶 Beginner-Friendly**: Explanations in simple language without jargon
- **⚡ Production Ready**: Modular, well-documented, and error-handled code

## 🏗️ Architecture

```
PDF Upload → OCR Processing → Text Cleaning → Semantic Chunking → Weaviate Storage
                                                                        ↓
User Query → Search → Single Best Match → Gemini 2.5 Pro → Simple Answer + Explanation
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- Google AI API Key

### 2. Installation

```bash
# Clone repository
git clone <repository-url>
cd pdf-policy-query-system

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configuration

Create a `.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Start the System

```bash
# Start everything automatically
python run_system.py
```

Or manually:
```bash
# Start Weaviate
docker-compose up -d

# Start backend (in terminal 1)
python backend.py

# Start frontend (in terminal 2)
cd frontend && npm start
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage

1. **Upload**: Drop a PDF policy document into the upload area
2. **Wait**: The system processes the document with OCR and text cleaning
3. **Ask**: Type your question in plain English
4. **Get Answer**: Receive a simple, clear explanation

### Example Queries

- "What is my deductible?"
- "Am I covered for dental work?"
- "How do I file a claim?"
- "What's the coverage limit for accidents?"

## 🔧 Technical Details

### OCR Processing

```python
class OCRProcessor:
    """Handles PDF OCR processing and text cleaning"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text with automatic OCR fallback"""
        # Direct text extraction first
        # OCR for image-based pages
        # Preprocessing for better accuracy
```

### Text Cleaning

- Removes duplicate lines
- Filters out page numbers and headers
- Normalizes punctuation and spacing
- Reorders fragmented text sections

### Single Answer Strategy

- Uses BM25 search to find the **single most relevant** chunk
- No multiple results to confuse users
- Focused, actionable responses

### Beginner-Friendly Responses

```python
class AnswerGenerator:
    """Generates simple explanations using Gemini 2.5 Pro"""
    
    # Structured prompts for consistent output
    # Simple language validation
    # Step-by-step explanations
```

## 📁 Project Structure

```
pdf-policy-query-system/
├── backend.py              # Main FastAPI application
├── requirements.txt        # Python dependencies
├── run_system.py          # Automated startup script
├── docker-compose.yml     # Weaviate configuration
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── App.css        # Production styling
│   └── package.json       # Node.js dependencies
└── README.md              # This file
```

## 🔍 API Endpoints

### POST /upload
Process and store a PDF document.

**Request**: Multipart form with PDF file
**Response**:
```json
{
  "message": "Successfully processed document.pdf",
  "chunks_created": 15,
  "text_length": 5420
}
```

### POST /query
Query documents and get simple answers.

**Request**:
```json
{
  "query": "What is my coverage limit?"
}
```

**Response**:
```json
{
  "answer": "Your coverage limit is $100,000 per incident",
  "explanation": "This means if you have an accident or need medical care, your insurance will pay up to $100,000 to cover the costs. This is the maximum amount they will pay for each separate incident.",
  "source": "policy.pdf"
}
```

## ⚙️ Configuration

### Weaviate Settings
- Vectorizer: `text2vec-transformers`
- Pooling: `masked_mean`
- Schema: Optimized for policy documents

### Text Processing
- Chunk size: 600 characters
- Overlap: 100 characters
- Minimum chunk length: 50 characters

### OCR Settings
- Primary: Tesseract with preprocessing
- Fallback: EasyOCR
- Image resolution: 2x for better accuracy

## 🚨 Troubleshooting

### Common Issues

**"No text extracted from PDF"**
- Ensure PDF is not corrupted
- Install Tesseract: `brew install tesseract` (macOS) or download from GitHub (Windows)

**"Weaviate connection failed"**
- Check Docker is running: `docker ps`
- Restart Weaviate: `docker-compose restart`

**"API key not configured"**
- Verify `.env` file exists and contains valid Google API key
- Ensure the key has Gemini API access

### Performance Tips

- Use clear, high-resolution PDFs for best OCR results
- Ask specific questions rather than general ones
- Keep policy documents focused (avoid mixing different types)

## 🧪 Testing

```bash
# Test backend health
curl http://localhost:8000/

# Test document upload
curl -X POST -F "file=@sample.pdf" http://localhost:8000/upload

# Test query
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"What is covered?"}' \
  http://localhost:8000/query
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes with proper documentation
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Google Gemini 2.5 Pro** for natural language processing
- **Weaviate** for vector search capabilities
- **PyMuPDF** for reliable PDF processing
- **FastAPI** for high-performance web framework