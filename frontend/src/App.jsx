import { useState } from 'react'
import './App.css'

function App() {
  // Tracks the name of the uploaded file, start empy when loaded
  const [uploadedFile, setUploadedFile] = useState('')

// Runs when file is selected and starts at the first file if multiple are uploaded
  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    // Updates useState for uploaded file so that UI displays the file name
    if (file) {
      setUploadedFile(file.name)
    }
  }
// Enter main flow of the app 
  return (
    <div className="app">
      {/* Header */}
      <header className="header-bar">
        <h1 className="logo">DocScanner<span>AI</span></h1>
      </header>

      {/* MAIN CONTAINER */}
      <div className="container">

        {/* LEFT PANEL */}
        <div className="left-panel">
          <h2>Upload Document</h2>
          <p className="panel-description">
            Upload a PDF or text file to ask questions about its content
          </p>

          <div className="upload-box">
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={handleFileUpload}
              id="file-box"
            />
            <label htmlFor="file-box">
              <div className="upload-icon">📄</div>
              <p>Click to upload or drag and drop</p>
              <span>PDF, TXT, or DOCX files only</span>
            </label>
          </div>

          {uploadedFile && (
            <div className="file-name">
               {uploadedFile}
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="right-panel">
          <div className="chat-window">
            <div className="chat-placeholder">
              <p>Upload a document to get started</p>
            </div>
          </div>

          <div className="chat-input-area">
            <textarea
              type="text"
              placeholder="Ask a question about your document"
              className="chat-input"
            />
            <button className="send-button">Send</button>
          </div>
        </div>

      </div>
    </div>
  )
}


export default App
