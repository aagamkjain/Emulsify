import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [activeSection, setActiveSection] = useState('documents');
  const [files, setFiles] = useState([]);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [reasoningData, setReasoningData] = useState(null);

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const validFiles = selectedFiles.filter(file => file.type === 'application/pdf');
    
    if (validFiles.length === 0) {
      setUploadStatus('Please select PDF files only');
      return;
    }
    
    if (validFiles.length > 3) {
      setUploadStatus('Maximum 3 PDF files allowed');
      return;
    }
    
    setFiles(validFiles);
    setUploadStatus('');
  };

  const removeFile = (index) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setUploadStatus('Please select at least one PDF file');
      return;
    }

    setIsUploading(true);
    setUploadStatus(`📄 Processing ${files.length} PDF file(s)...`);

    try {
      // Try multiple file upload first
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      let response;
      try {
        response = await axios.post(`${API_BASE_URL}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } catch (multiError) {
        console.log('Multiple upload failed, trying individual uploads:', multiError);
        
        // Fallback: upload files one by one
        const processedDocs = [];
        for (let i = 0; i < files.length; i++) {
          const singleFormData = new FormData();
          singleFormData.append('file', files[i]);
          
          setUploadStatus(`📄 Processing file ${i + 1}/${files.length}: ${files[i].name}`);
          
          const singleResponse = await axios.post(`${API_BASE_URL}/upload-single`, singleFormData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          
          processedDocs.push({
            filename: files[i].name,
            chunks_created: singleResponse.data.chunks_created,
            text_length: singleResponse.data.text_length
          });
        }
        
        response = {
          data: {
            message: `Successfully processed ${processedDocs.length} document(s)`,
            documents: processedDocs,
            total_documents: processedDocs.length
          }
        };
      }

      setUploadedDocuments(response.data.documents);
      setUploadStatus(`✅ ${response.data.message}`);
      setFiles([]); // Clear selected files
      
      // Clear success message after 5 seconds
      setTimeout(() => setUploadStatus(''), 5000);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Error uploading files';
      setUploadStatus(`❌ ${errorMessage}`);
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const clearAllDocuments = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/documents`);
      setUploadedDocuments([]);
      setUploadStatus('✅ All documents cleared');
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Error clearing documents';
      setUploadStatus(`❌ ${errorMessage}`);
      console.error('Clear error:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      return;
    }

    setIsSearching(true);
    setSearchResults(null);

    try {
      console.log('Searching for:', searchQuery);
      
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: searchQuery
      });

      console.log('Search response:', response.data);
      setSearchResults(response.data);
      
      // Store data for reasoning section
      setReasoningData({
        query: searchQuery,
        results: response.data,
        timestamp: new Date().toISOString(),
        uploadedDocuments: uploadedDocuments
      });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Error searching documents';
      console.error('Search error:', errorMessage);
      const errorResults = {
        answer: 'Search Error',
        explanation: errorMessage,
        confidence: 0
      };
      setSearchResults(errorResults);
      
      // Store error data for reasoning section
      setReasoningData({
        query: searchQuery,
        results: errorResults,
        timestamp: new Date().toISOString(),
        uploadedDocuments: uploadedDocuments,
        error: true
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const renderDashboard = () => (
    <div className="dashboard-content">
      <div className="dashboard-guide">
        <h3>Welcome to Emulsify</h3>
        <p>Intelligent document analysis and query system powered by AI</p>
      </div>
    </div>
  );

  const renderReasoning = () => (
    <div className="main-content">
      <div className="reasoning-card">
        <div className="reasoning-header">
          <h2>🧠 Detailed Reasoning Analysis</h2>
          <p>Deep dive into how your query was processed and analyzed</p>
        </div>
        
        <div className="reasoning-content">
          {!reasoningData ? (
            <div className="no-reasoning-data">
              <div className="no-data-icon">🤔</div>
              <h3>No Analysis Available</h3>
              <p>Perform a query in the Document Analysis section to see detailed reasoning here.</p>
              <button 
                onClick={() => setActiveSection('documents')}
                className="go-to-documents-btn"
              >
                Go to Document Analysis
              </button>
            </div>
          ) : (
            <div className="reasoning-analysis">
              {/* Query Breakdown Section */}
              <div className="analysis-section">
                <h3>📝 Query Breakdown</h3>
                <div className="query-breakdown">
                  <div className="original-query">
                    <h4>Original Query:</h4>
                    <div className="query-text">"{reasoningData.query}"</div>
                  </div>
                  
                  <div className="query-analysis">
                    <h4>Query Analysis:</h4>
                    <div className="analysis-points">
                      <div className="analysis-point">
                        <span className="point-label">Query Type:</span>
                        <span className="point-value">
                          {reasoningData.query.toLowerCase().includes('compare') || reasoningData.query.toLowerCase().includes('difference') 
                            ? 'Comparative Analysis' 
                            : reasoningData.query.toLowerCase().includes('what') || reasoningData.query.toLowerCase().includes('how')
                            ? 'Information Retrieval'
                            : reasoningData.query.toLowerCase().includes('does') || reasoningData.query.toLowerCase().includes('is')
                            ? 'Yes/No Query'
                            : 'General Inquiry'}
                        </span>
                      </div>
                      <div className="analysis-point">
                        <span className="point-label">Key Terms:</span>
                        <span className="point-value">
                          {reasoningData.query.split(' ')
                            .filter(word => word.length > 3)
                            .filter(word => !['what', 'how', 'does', 'the', 'and', 'are', 'this', 'that', 'with', 'from'].includes(word.toLowerCase()))
                            .slice(0, 5)
                            .join(', ')}
                        </span>
                      </div>
                      <div className="analysis-point">
                        <span className="point-label">Document Scope:</span>
                        <span className="point-value">
                          {reasoningData.results.sources ? 
                            `${reasoningData.results.sources.length} document(s) analyzed` : 
                            'Single document analysis'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Processing Method Section */}
              <div className="analysis-section">
                <h3>⚙️ Processing Method</h3>
                <div className="processing-method">
                  <div className="method-steps">
                    <div className="step">
                      <div className="step-number">1</div>
                      <div className="step-content">
                        <h4>Document Chunking</h4>
                        <p>Documents were split into semantic chunks for better analysis. Total documents processed: <strong>{reasoningData.uploadedDocuments.length}</strong></p>
                      </div>
                    </div>
                    <div className="step">
                      <div className="step-number">2</div>
                      <div className="step-content">
                        <h4>Semantic Search</h4>
                        <p>Used BM25 algorithm to find the most relevant chunks based on your query terms and context.</p>
                      </div>
                    </div>
                    <div className="step">
                      <div className="step-number">3</div>
                      <div className="step-content">
                        <h4>AI Analysis</h4>
                        <p>Applied advanced language model (Gemini) to analyze retrieved content and generate comprehensive answers.</p>
                      </div>
                    </div>
                    {reasoningData.results.cross_document_analysis && (
                      <div className="step">
                        <div className="step-number">4</div>
                        <div className="step-content">
                          <h4>Cross-Document Synthesis</h4>
                          <p>Compared and synthesized information across multiple documents to provide comprehensive insights.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Sources Analysis Section */}
              {reasoningData.results.sources && reasoningData.results.sources.length > 0 && (
                <div className="analysis-section">
                  <h3>📚 Source Documents Analysis</h3>
                  <div className="sources-analysis">
                    {reasoningData.results.sources.map((source, index) => {
                      const docInfo = reasoningData.uploadedDocuments.find(doc => doc.filename === source);
                      return (
                        <div key={index} className="source-analysis">
                          <div className="source-header">
                            <span className="source-name">{source}</span>
                            {docInfo && (
                              <span className="source-stats">
                                {docInfo.chunks_created} chunks • {(docInfo.text_length / 1000).toFixed(1)}k chars
                              </span>
                            )}
                          </div>
                          <div className="source-contribution">
                            <strong>Contribution to Answer:</strong> This document provided relevant information that was used to formulate the response.
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Answer Confidence Section */}
              <div className="analysis-section">
                <h3>🎯 Answer Confidence & Quality</h3>
                <div className="confidence-analysis">
                  <div className="confidence-metrics">
                    <div className="metric">
                      <span className="metric-label">Source Reliability:</span>
                      <span className="metric-value">
                        {reasoningData.results.sources && reasoningData.results.sources.length > 1 ? 'High (Multiple Sources)' : 'Medium (Single Source)'}
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Answer Completeness:</span>
                      <span className="metric-value">
                        {reasoningData.results.answer && reasoningData.results.answer.length > 100 ? 'Comprehensive' : 'Concise'}
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Cross-Reference:</span>
                      <span className="metric-value">
                        {reasoningData.results.cross_document_analysis ? 'Available' : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Explanation Section */}
              <div className="analysis-section">
                <h3>🔍 Detailed Explanation Breakdown</h3>
                <div className="explanation-breakdown">
                  <div className="explanation-text">
                    <h4>How the Answer was Formulated:</h4>
                    <div className="explanation-content">
                      {reasoningData.results.explanation && (
                        <p>{reasoningData.results.explanation}</p>
                      )}
                      
                      {reasoningData.results.cross_document_analysis && (
                        <div className="cross-doc-reasoning">
                          <h4>Cross-Document Reasoning:</h4>
                          <p>{reasoningData.results.cross_document_analysis}</p>
                        </div>
                      )}
                      
                      <div className="reasoning-summary">
                        <h4>Summary of Reasoning Process:</h4>
                        <ul>
                          <li>Your query was analyzed to identify key information requirements</li>
                          <li>Relevant document sections were retrieved using semantic search</li>
                          <li>AI model processed the context to understand relationships and implications</li>
                          {reasoningData.results.sources && reasoningData.results.sources.length > 1 && (
                            <li>Multiple sources were cross-referenced to ensure comprehensive coverage</li>
                          )}
                          <li>The final answer was synthesized to directly address your specific question</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Query Metadata */}
              <div className="analysis-section">
                <h3>📊 Query Metadata</h3>
                <div className="metadata">
                  <div className="metadata-item">
                    <span className="metadata-label">Query Time:</span>
                    <span className="metadata-value">{new Date(reasoningData.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="metadata-label">Documents Available:</span>
                    <span className="metadata-value">{reasoningData.uploadedDocuments.length}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="metadata-label">Query Length:</span>
                    <span className="metadata-value">{reasoningData.query.length} characters</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderDocumentAnalysis = () => (
    <div className="main-content">
      <div className="document-analysis-card">
        <div className="analysis-header">
          <h2>Document Analysis</h2>
          <p>Upload up to 3 documents and get intelligent cross-document insights through natural language queries</p>
        </div>
        
        <div className="analysis-content">
          {/* Upload Section */}
          <div className="upload-section">
            <div className="section-header">
              <h3>📤 Upload Documents (Max 3 PDFs)</h3>
              {uploadedDocuments.length > 0 && (
                <button onClick={clearAllDocuments} className="clear-btn">
                  🗑️ Clear All
                </button>
              )}
            </div>
            
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileSelect}
                className="file-input"
                id="file-input"
              />
              <label htmlFor="file-input" className="file-label">
                {files.length > 0 ? (
                  <div className="files-selected">
                    <div className="files-header">
                      <div className="upload-icon">📁</div>
                      <div className="upload-text">{files.length} PDF file(s) selected</div>
                    </div>
                    <div className="files-list">
                      {files.map((file, index) => (
                        <div key={index} className="file-item">
                          <div className="file-info">
                            <div className="file-name">{file.name}</div>
                            <div className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</div>
                          </div>
                          <button 
                            onClick={(e) => {
                              e.preventDefault();
                              removeFile(index);
                            }}
                            className="remove-file-btn"
                          >
                            ❌
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="file-placeholder">
                    <div className="upload-icon">📁</div>
                    <div className="upload-text">Choose PDF Documents</div>
                    <div className="upload-subtext">Select up to 3 PDF documents for cross-document analysis</div>
                  </div>
                )}
              </label>
              
              {files.length > 0 && (
                <button 
                  onClick={handleUpload} 
                  disabled={isUploading}
                  className="upload-btn"
                >
                  {isUploading ? (
                    <>
                      <span className="loading-spinner"></span>
                      Processing...
                    </>
                  ) : (
                    `📤 Process ${files.length} Document(s)`
                  )}
                </button>
              )}
            </div>
            
            {uploadStatus && (
              <div className={`status-message ${uploadStatus.includes('❌') ? 'error' : 'success'}`}>
                {uploadStatus}
              </div>
            )}

            {/* Uploaded Documents Display */}
            {uploadedDocuments.length > 0 && (
              <div className="uploaded-docs">
                <h4>📚 Uploaded Documents ({uploadedDocuments.length}/3)</h4>
                <div className="docs-list">
                  {uploadedDocuments.map((doc, index) => (
                    <div key={index} className="doc-item">
                      <div className="doc-icon">📄</div>
                      <div className="doc-info">
                        <div className="doc-name">{doc.filename}</div>
                        <div className="doc-stats">{doc.chunks_created} chunks • {(doc.text_length / 1000).toFixed(1)}k chars</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Query Section */}
          <div className="query-section">
            <h3>🔍 Ask Questions</h3>
            <div className="query-description">
              {uploadedDocuments.length > 1 ? 
                "Ask questions that span across multiple documents for comprehensive analysis" :
                "Ask any question about your uploaded document"
              }
            </div>
            <div className="search-area">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={uploadedDocuments.length > 1 ? 
                  "e.g., Compare coverage between documents, What are the differences in policies?" :
                  "Ask any question about your document..."
                }
                className="search-input"
              />
              <button 
                onClick={handleSearch}
                disabled={!searchQuery.trim() || isSearching || uploadedDocuments.length === 0}
                className="search-btn"
              >
                {isSearching ? (
                  <>
                    <span className="loading-spinner"></span>
                    Analyzing...
                  </>
                ) : (
                  'Ask'
                )}
              </button>
            </div>
          </div>

          {/* Results Section */}
          {searchResults && (
            <div className="results-section">
              <h3>💡 Analysis Results</h3>
              <div className="result-card">
                {searchResults.sources && searchResults.sources.length > 0 && (
                  <div className="sources-info">
                    <span className="sources-label">Sources ({searchResults.sources.length}):</span>
                    <div className="sources-list">
                      {searchResults.sources.map((source, index) => (
                        <span key={index} className="source-tag">{source}</span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="answer-section">
                  <div className="answer-content">
                    {searchResults.answer}
                  </div>
                </div>
                
                <div className="explanation-section">
                  <div className="explanation-content">
                    {searchResults.explanation}
                  </div>
                </div>

                {searchResults.cross_document_analysis && (
                  <div className="cross-analysis-section">
                    <h4 className="cross-analysis-title">🔄 Cross-Document Analysis</h4>
                    <div className="cross-analysis-content">
                      {searchResults.cross_document_analysis}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon">🔬</div>
          <div className="logo-text">
            <div className="logo-title">Emulsify</div>
            <div className="logo-subtitle">Intelligent Document Analysis</div>
          </div>
        </div>

        <nav className="nav-menu">
          <div 
            className={`nav-item ${activeSection === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveSection('dashboard')}
          >
            <span className="nav-icon">📊</span>
            <span>DASHBOARD</span>
          </div>
          
          <div 
            className={`nav-item ${activeSection === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveSection('documents')}
          >
            <span className="nav-icon">📄</span>
            <span>Document Analysis</span>
          </div>

          <div 
            className={`nav-item ${activeSection === 'reasoning' ? 'active' : ''}`}
            onClick={() => setActiveSection('reasoning')}
          >
            <span className="nav-icon">🧠</span>
            <span>Reasoning</span>
          </div>
        </nav>

        <div className="sidebar-footer">
          <button className="sign-out-btn">
            ↗ Sign Out
          </button>
          <p className="session-info">Your session will be securely terminated</p>
        </div>
      </div>

      <div className="main-container">
        {activeSection === 'dashboard' && renderDashboard()}
        {activeSection === 'documents' && renderDocumentAnalysis()}
        {activeSection === 'reasoning' && renderReasoning()}
      </div>
    </div>
  );
}

export default App;