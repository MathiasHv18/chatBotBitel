const express = require('express');
const axios = require('axios');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 4000;


app.post('', async (req, res) => {
  try {
    const { message, history } = req.body;
    
    if (!process.env.OPENAI_API_KEY) {
      return res.status(500).json({ error: "Missing OpenAI API Key" });
    }
    
    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
        model: 'gpt-3.5-turbo', // or 'gpt-4' if you have access
        messages: history.concat({ role: 'user', content: message })
      }, {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      });
    
    res.json(response.data);
  } catch (error) {
    console.error("Error:", error.response ? error.response.data : error.message);
    res.status(error.response?.status || 500).json({ 
      error: error.response?.data?.error?.message || "Internal Server Error" 
    });
  }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));