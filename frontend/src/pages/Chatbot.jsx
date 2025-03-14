import React, { useState } from 'react'
import './Chatbot.css'
import axios from 'axios'; // Or your custom axios config

function Chatbot() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  const sendPrompt = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    
    setChatHistory([...chatHistory, { sender: 'user', content: message }]);
    setMessage('');
    setLoading(true);
    
    try {
      const response = await axios.post('http://localhost:4000/api/chat', {
        message: message,
        history: chatHistory.map(chat => ({
          role: chat.sender === 'user' ? 'user' : 'assistant',
          content: chat.content
        }))
      });
      
      const botMessage = response.data.response || 'No response';
      setChatHistory(prevHistory => [...prevHistory, { sender: 'bot', content: botMessage }]);
    } catch (error) {
      console.error('Error:', error);
      setChatHistory(prevHistory => [...prevHistory, { 
        sender: 'system', 
        content: `Error: ${error.response?.data?.error || 'Could not get response'}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-box">
        {chatHistory.map((chat, index) => (
          <div key={index} className={`chat-message ${chat.sender}`}>
            <p>{chat.content}</p>
          </div>
        ))}
        {loading && <div className="chat-message system"><p>Loading...</p></div>}
      </div>
      <form onSubmit={sendPrompt} className="chat-form">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="chat-input"
          placeholder="Type your message..."
          disabled={loading}
        />
        <button
          type="submit"
          className="chat-button"
          disabled={loading || !message.trim()}
        >
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  )
}

export default Chatbot