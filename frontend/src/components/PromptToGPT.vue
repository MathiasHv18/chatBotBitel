<template>
  <div :class="['appContainer', isDarkMode ? 'dark-mode' : 'light-mode']">
    <div class="sidebar">
      <div class="sidebarHeader">
        <h2>Chat History</h2>
        <button class="newChatButton">+ New Chat</button>
      </div>
      <ul>
        <li
          v-for="chat in chatHistory"
          :key="chat"
          @click="getUserChat(chat)"
          :class="{ selectedChat: chat === selectedChatId }"
          @mouseenter="hoveredChat = chat"
          @mouseleave="hoveredChat = null"
        >
          Conversation number {{ chat }}
          <span
            v-if="hoveredChat === chat"
            class="chatOptions"
            @click.stop="showDeleteOption(chat)"
          >
            ⋮
          </span>
          <div
            v-if="deleteOption === chat"
            class="deleteChat"
            @click.stop="cleanHistory(chat)"
          >
            Eliminar chat
          </div>
        </li>
      </ul>
    </div>
    <div class="chatContainer">
      <div class="topBar">
        <button @click="toggleDarkMode" class="modeToggle">
          {{ isDarkMode ? "🌙 Dark Mode" : "☀️ Light Mode" }}
        </button>
        <select
          v-model="modelUsing"
          @change="chooseModel(modelUsing)"
          class="modelSelector"
        >
          <option :value="1">DeepSeek</option>
          <option :value="2">ChatGPT</option>
        </select>
        <button @click="toggleChurn" class="churnToggle">
          {{ isChurn ? "Predicting Churn" : "Not predicting Churn" }}
        </button>
      </div>

      <div class="messages">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="{ userMessage: msg.isUser, botMessage: !msg.isUser }"
        >
          <span v-html="msg.text"></span>
        </div>
      </div>
      <div class="inputContainer">
        <textarea
          v-model="userPrompt"
          placeholder="Ask anything"
          ref="textareaRef"
          @input="adjustTextareaHeight"
          @keydown.enter.exact.prevent="sendPrompt"
          @keydown.enter.shift.prevent="newLine"
        ></textarea>
        <button @click="sendPrompt">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="white">
            <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from "vue";
import { watch } from "vue";

import "./PromptToGPT.css";

const errorMessage = ref("");
const showError = ref(false);
const username = ref(null);
const modelUsing = ref(2);
const userPrompt = ref("");
const messages = ref([]);
const isDarkMode = ref(true);
const loading = ref(false);
const isChurn = ref(false);
const chatBox = ref(null);
const chatHistory = ref([]);
const textareaRef = ref(null);
const selectedChatId = ref(null);
const hoveredChat = ref(null);
const deleteOption = ref(null);

//prod :(
const api = "http://10.121.30.150:8000";
//home office :)
//const api = "http://127.0.0.1:8000";

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
};
const showDeleteOption = (chat) => {
  deleteOption.value = deleteOption.value === chat ? null : chat;
};

const cleanHistory = async (chat) => {
  await fetch(`${api}/api/clear_conversation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: chat }),
  });
  chatHistory.value = chatHistory.value.filter((c) => c !== chat);
  deleteOption.value = null;
};

watch(userPrompt, () => {
  nextTick(() => {
    adjustTextareaHeight();
  });
});

const showNotification = (message) => {
  errorMessage.value = message;
  showError.value = true;
  setTimeout(() => {
    showError.value = false;
    errorMessage.value = "";
  }, 5000);
};

const adjustTextareaHeight = () => {
  if (!textareaRef.value) return;
  const textarea = textareaRef.value;

  textarea.style.height = "auto";

  textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
};

const newLine = (event) => {
  event.preventDefault();
  userPrompt.value += "\n";
};

const getUserChat = async (chat) => {
  cleanScreen();
  selectedChatId.value = chat;
  try {
    const response = await fetch(`${api}/api/chatUser`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: String(chat) }),
    });

    if (!response.ok) {
      throw new Error(`Error en la solicitud: ${response.status}`);
    }

    const data = await response.json();

    messages.value = [];
    console.log("Mensajes recibidos:", data.response);

    data.response.forEach((msg) => {
      console.log(`Role: ${msg.role}, Content: ${msg.content}`);
    });

    messages.value = data.response.map((msg) => ({
      text: msg.content,
      isUser: msg.role === "user",
    }));
  } catch (error) {
    console.error("Error al obtener chats:", error);
  }
};

const toggleChurn = () => {
  isChurn.value = !isChurn.value;
};

onMounted(async () => {
  await chooseModel(2);
  await getChats();
});

const cleanScreen = () => {
  messages.value = [];
};

const chooseModel = async (model) => {
  cleanScreen();
  const response = await fetch(`${api}/api/lastChat`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  let lastUsername = await response.json();
  username.value = (parseInt(lastUsername.response) + 1).toString();
  console.log(username.value, typeof username.value);
  modelUsing.value = model;
  await fetch(`${api}/api/inputModel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modelUser: model, username: username.value }),
  });
  getChats();
};

const handleEnter = (event) => {
  if (event.shiftKey) {
    userPrompt.value += "\n";
  } else {
    sendPrompt();
  }
};

const getChats = async () => {
  const response = await fetch(`${api}/api/getAllChats`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  const data = await response.json();
  chatHistory.value = data.chat_ids;
};

const sendPrompt = async () => {
  if (!userPrompt.value) return;
  const promptText = userPrompt.value;
  userPrompt.value = "";

  if (textareaRef.value) {
    adjustTextareaHeight();
  }

  messages.value.push({ text: promptText, isUser: true });

  const typingMessage = { text: "Typing...", isUser: false };
  messages.value.push(typingMessage);
  loading.value = true;

  await nextTick(() => {
    if (chatBox.value) {
      chatBox.value.scrollTop = chatBox.value.scrollHeight;
    }
  });

  try {
    const response = await fetch(`${api}/api/query_database`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptText,
        modelUser: modelUsing.value,
        username: username.value,
        isChurn: isChurn.value,
      }),
    });

    const data = await response.json();
    const formattedResponse = data.response
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, "<code>$1</code>")
      .replace(/\n/g, "<br>");

    messages.value.splice(messages.value.indexOf(typingMessage), 1, {
      text: formattedResponse,
      isUser: false,
    });

    await nextTick(() => {
      if (chatBox.value) {
        chatBox.value.scrollTop = chatBox.value.scrollHeight;
      }
    });
  } catch (err) {
    console.error("Error fetching response:", err);
    messages.value.splice(messages.value.indexOf(typingMessage), 1, {
      text: "Error getting response",
      isUser: false,
    });
  } finally {
    loading.value = false;
  }
};
</script>
