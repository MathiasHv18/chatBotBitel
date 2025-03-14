import {React, useState} from 'react'
import './Chatbot.css'
import axios from 'axios';

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
      const response = await axios.post('/api/query_database', { prompt: message });
      if (response.data.response) {
        setChatHistory(prevHistory => [
          ...prevHistory,
          { sender: 'bot', content: response.data.response }
        ]);
      } else {
        setChatHistory(prevHistory => [
          ...prevHistory,
          { sender: 'system', content: response.data.error || "Unknown error" }
        ]);
      }
    } catch (error) {
      setChatHistory(prevHistory => [
        ...prevHistory,
        { sender: 'system', content: "Error: Could not get response" }
      ]);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="chat-container">
      <div className="chat-box">
        {chatHistory.map((chat, index) => (
          <div key={index} className={chat.sender === 'user' ? 'chat-message user' : 'chat-message bot'}>
            <p>{chat.content}</p>
          </div>
        ))}
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
          disabled={loading}
        >
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  )
}

export default Chatbot