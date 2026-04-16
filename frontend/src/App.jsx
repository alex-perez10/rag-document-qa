import { useState } from 'react'
import './App.css'

function App() {
const [uploadedFile, setUploadedFile] = useState(null)
const [fileName, setFileName] = useState('')
const [messages, setMessages] = useState([])
const [history, setHistory] = useState([])
const [question, setQuestion] = useState('')
const [isLoading, setIsLoading] = useState(false)

// Runs when file is selected and starts at the first file if multiple are uploaded
  const handleFileUpload = (e) => {
  const file = e.target.files[0]
  if (file) {
    setUploadedFile(file)
    setFileName(file.name)
    handleSendFile(file)
  }
}
// Sends file to the backend
const handleSendFile = async (file) => {
  // Packages the file into a format the backend can receive
  const formData = new FormData()
  formData.append('file', file)
   try {
    const response = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()
  } catch (error) {
    console.error('Upload failed:', error)
  }
}

const handleSendMessage = async () => {
  // Message doesn't send if question is empty or no file uploaded
  if (!question.trim() || !uploadedFile) return

  // Assigns role and content how backend expects
  const userMessage = { role: 'user', content: question }
  // Displays conversation in UI
  setMessages(prev => [...prev, userMessage])
  setQuestion('')
  setIsLoading(true)

  try {
    // Sends a request to backend using JSON
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history })
    })
    const data = await response.json()

    const assistantMessage = { role: 'assistant', content: data.answer }
    // Builds context by adding message to previous message and then history
    setMessages(prev => [...prev, assistantMessage])
    setHistory(prev => [...prev, userMessage, assistantMessage])
  } catch (error) {
    console.error('Chat failed:', error)
  } finally {
    setIsLoading(false)
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
               {fileName}
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
<div className="right-panel">
  <div className="chat-window">
    {messages.length === 0 ? (
      <div className="chat-placeholder">
        <p>Upload a document to get started</p>
      </div>
    ) : (
      messages.map((msg, index) => (
        <div key={index} className={`message ${msg.role}`}>
          <p>{msg.content}</p>
        </div>
      ))
    )}
    {isLoading && (
      <div className="message assistant">
        <p>Thinking...</p>
      </div>
    )}
  </div>

  <div className="chat-input-area">
    <textarea
      placeholder="Ask a question about your document"
      className="chat-input"
      value={question}
      onChange={(e) => setQuestion(e.target.value)}
    />
    <button className="send-button" onClick={handleSendMessage}>Send</button>
  </div>
</div>
</div>
    </div>
  )
}


export default App
