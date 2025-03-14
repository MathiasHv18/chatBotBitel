import { useState } from 'react';
import axios from 'axios';
import './App.css';
import Chatbot from './pages/Chatbot';
import Chats from './pages/Chats';

function App() {
  return (
    <div className="body">
    <Chats />
    <Chatbot />
    </div>
  );
}

export default App;
