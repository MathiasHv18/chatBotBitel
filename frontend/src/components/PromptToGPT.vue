<template>
  <div :class="['appContainer', isDarkMode ? 'dark-mode' : 'light-mode']">
    <div class="sidebar">
      <div class="sidebarHeader">
        <h2>Chat History</h2>
        <button class="newChatButton" @click="chooseModel(2)">
          + New Chat
        </button>
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
          Conversation #{{ chat }}
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
            Delete chat
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
          {{ isChurn ? "Predicting Churn" : "Not Predicting Churn" }}
        </button>
      </div>

      <div class="messages" ref="messagesContainer">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="{ userMessage: msg.isUser, botMessage: !msg.isUser }"
        >
          <span v-if="msg.isUser" v-html="formatMessageText(msg.text)"></span>
          <span
            v-else
            v-html="msg.isTyping ? msg.text : formatMessageText(msg.text)"
          ></span>
        </div>
      </div>
      <div v-if="selectedImages.length" class="imagePreviewContainer">
        <div
          v-for="(image, index) in selectedImages"
          :key="index"
          class="imagePreview"
        >
          <img :src="image" alt="Preview" class="previewImage" />
          <button @click="removeImage(index)">✖</button>
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

        <div class="file-upload-container">
          <input
            type="file"
            ref="fileInput"
            @change="handleImageUpload"
            accept="image/*"
            multiple
          />
          <button
            type="button"
            class="custom-file-upload"
            @click="$refs.fileInput.click()"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path
                d="M4 4h3l2-2h6l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m8 3a4 4 0 0 0-4 4a4 4 0 0 0 4 4a4 4 0 0 0 4-4a4 4 0 0 0-4-4m0 2a2 2 0 0 1 2 2a2 2 0 0 1-2 2a2 2 0 0 1-2-2a2 2 0 0 1 2-2Z"
              />
            </svg>
          </button>
        </div>
        <button @click="sendPrompt">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="white">
            <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"></path>
          </svg>
        </button>
      </div>
    </div>
    <template>
      <div class="errorNotification" v-if="errorMessage">
        {{ errorMessage }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from "vue";
import { watch } from "vue";

import "./PromptToGPT.css";

const messagesContainer = ref(null);
const selectedImages = ref([]);
const errorMessage = ref("");
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
//const api = "http://10.121.30.150:8000";
//home office :)
const api = "http://127.0.0.1:8000";

onMounted(async () => {
  await chooseModel(2);
  await getChats();
  document.addEventListener("paste", handlePaste);
});

onUnmounted(() => {
  document.removeEventListener("paste", handlePaste);
});

const formatMessageText = (text) => {
  if (!text) return "";

  if (typeof text === "object" && text.images && text.text) {
    const images = text.images;
    const messageText = text.text;

    const imagesHtml = `
      <div class="message-image-container">
        ${images
          .map(
            (image) =>
              `<img src="${image}" alt="Message Image" class="message-image"/>`
          )
          .join("")}
      </div>
    `;

    return `${imagesHtml}${formatMessage(messageText)}`;
  }

  return formatMessage(text);
};
// Function to handle images pasted with Ctrl + V
const handlePaste = (event) => {
  const items = event.clipboardData.items;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const file = item.getAsFile();
      const reader = new FileReader();
      reader.onload = (e) => {
        selectedImages.value.push(e.target.result); // Save the image in Base64
      };
      reader.readAsDataURL(file);
    }
  }
};

watch(userPrompt, () => {
  nextTick(() => {
    adjustTextareaHeight();
  });
});

const removeImage = (index) => {
  selectedImages.value.splice(index, 1);
};

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
};
const showDeleteOption = (chat) => {
  deleteOption.value = deleteOption.value === chat ? null : chat;
};

const cleanHistory = async (chat) => {
  console.log(chat);
  await fetch(`${api}/api/clear_conversation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: String(chat) }),
  });
  chatHistory.value = chatHistory.value.filter((c) => c !== chat);
  deleteOption.value = null;
};

const showError = (message) => {
  errorMessage.value = message;
  setTimeout(() => {
    errorMessage.value = "";
  }, 3000); // Disappears in 3 seconds
};

const adjustTextareaHeight = () => {
  if (!textareaRef.value) return;
  const textarea = textareaRef.value;
  const inputContainer = textarea.closest(".inputContainer");

  textarea.style.height = "auto";

  const maxHeight = 200;

  if (textarea.scrollHeight > maxHeight) {
    textarea.style.height = `${maxHeight}px`;
    textarea.style.overflowY = "auto";
    inputContainer.style.overflowY = "auto";
  } else {
    textarea.style.height = `${textarea.scrollHeight}px`;
    textarea.style.overflowY = "hidden";
    inputContainer.style.overflowY = "hidden";
  }
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
      throw new Error(`Request error: ${response.status}`);
    }

    const data = await response.json();
    messages.value = data.response.map((msg) => ({
      text: msg.content,
      isUser: msg.role === "user",
    }));

    await nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop =
          messagesContainer.value.scrollHeight;
      }
    });
  } catch (error) {
    console.error("Error getting chats:", error);
  }
};
const toggleChurn = () => {
  isChurn.value = !isChurn.value;
};

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

  modelUsing.value = model;

  await fetch(`${api}/api/inputModel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      modelUser: model,
      username: String(username.value),
    }),
  });

  await new Promise((resolve) => setTimeout(resolve, 500));

  await getChats();

  if (chatHistory.value.length > 0) {
    selectedChatId.value = chatHistory.value[chatHistory.value.length - 1];
    getUserChat(selectedChatId.value);
  }
};

const getChats = async () => {
  const response = await fetch(`${api}/api/getAllChats`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  const data = await response.json();
  chatHistory.value = data.chat_ids;

  if (chatHistory.value.length > 0) {
    selectedChatId.value = chatHistory.value[chatHistory.value.length - 1];
    getUserChat(selectedChatId.value);
  }
};

const handleImageUpload = (event) => {
  const files = event.target.files;
  if (!files.length) return;

  Array.from(files).forEach((file) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      selectedImages.value.push(reader.result);
    };
  });

  event.target.value = "";
};

// Función para formatear el texto y detectar bloques de código
const formatMessage = (text) => {
  if (!text) return "";

  // Regex para detectar bloques de código con triple backtick
  const codeBlockRegex = /```([a-zA-Z]*)\n([\s\S]*?)```/g;

  // Reemplazar los bloques de código con divs formateados
  const formattedText = text.replace(
    codeBlockRegex,
    (match, language, code) => {
      return `<div class="code-block">
              <div class="code-header">
                <span class="code-language">${language || "code"}</span>
                <button class="copy-button" onclick="copyToClipboard(this)">Copy</button>
              </div>
              <pre><code class="${language || ""}">${escapeHtml(
        code
      )}</code></pre>
            </div>`;
    }
  );

  // Manejo de formato markdown básico (negritas, cursivas, etc.)
  return formattedText
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br>");
};

// Función para escapar HTML y evitar problemas de seguridad
const escapeHtml = (unsafe) => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

// Reemplaza la función copyToClipboard en el script
window.copyToClipboard = (button) => {
  const codeBlock = button.closest(".code-block").querySelector("code");
  const text = codeBlock.textContent;

  // Método alternativo para compatibilidad con HTTP
  const fallbackCopyTextToClipboard = (text) => {
    // Crear un elemento temporal
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Hacerlo invisible pero mantenerlo en el DOM
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.width = "2em";
    textArea.style.height = "2em";
    textArea.style.padding = "0";
    textArea.style.border = "none";
    textArea.style.outline = "none";
    textArea.style.boxShadow = "none";
    textArea.style.background = "transparent";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand("copy");
      if (!successful) {
        console.error("Fallback: No se pudo copiar");
      }
    } catch (err) {
      console.error("Fallback: No se pudo copiar", err);
    }

    document.body.removeChild(textArea);
  };

  // Intentar primero con la API Clipboard moderna
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        updateButtonState(button);
      })
      .catch(() => {
        // Si falla, usar el método alternativo
        fallbackCopyTextToClipboard(text);
        updateButtonState(button);
      });
  } else {
    // Para HTTP y navegadores antiguos
    fallbackCopyTextToClipboard(text);
    updateButtonState(button);
  }
};

// Función separada para actualizar el estado del botón
const updateButtonState = (button) => {
  const originalText = button.textContent;
  button.textContent = "Copied!";
  button.classList.add("copied");

  setTimeout(() => {
    button.textContent = originalText;
    button.classList.remove("copied");
  }, 2000);
};

const sendPrompt = async () => {
  if (!userPrompt.value && selectedImages.value.length === 0) return;
  const promptText = userPrompt.value;
  userPrompt.value = "";

  if (textareaRef.value) {
    adjustTextareaHeight();
  }

  const imagesToSend =
    selectedImages.value.length > 0 ? [...selectedImages.value] : [];

  // Structure user message with images if present
  const userMessage =
    imagesToSend.length > 0
      ? { text: promptText, images: imagesToSend }
      : promptText;

  messages.value.push({ text: userMessage, isUser: true });
  selectedImages.value = []; // Clear images after pushing to message

  // Usar el indicador de typing en HTML en lugar de texto plano
  const typingMessage = {
    text: '<div class="typing-indicator"><span></span><span></span><span></span></div>',
    isUser: false,
    isTyping: true,
  };
  messages.value.push(typingMessage);
  loading.value = true;

  // El resto de la función se mantiene igual...
  await nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });

  try {
    const response = await fetch(`${api}/api/query_database`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptText,
        modelUser: modelUsing.value,
        username: String(selectedChatId.value),
        isChurn: isChurn.value,
        images: imagesToSend,
      }),
    });

    const data = await response.json();

    messages.value.pop();

    if (data.error) {
      let errorMessage = data.error;
      if (
        typeof data.error === "string" &&
        data.error.includes("OpenAI API rate limit")
      ) {
        errorMessage =
          "The OpenAI API rate limit has been exceeded. Please try again later.";
      }

      messages.value.push({
        text: `⚠️ Error: ${errorMessage}`,
        isUser: false,
      });

      showError(errorMessage);
    } else {
      messages.value.push({ text: data.response, isUser: false });
    }

    console.log(data);
  } catch (err) {
    console.error("Error:", err);
    messages.value.pop();
    messages.value.push({
      text: `⚠️ Error: ${err.message}`,
      isUser: false,
    });
    showError(err.message);
  } finally {
    loading.value = false;
    await nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop =
          messagesContainer.value.scrollHeight;
      }
    });
  }
};

const generateImg = async () => {
  try {
    const response = await fetch(`${api}/api/generateImage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: "generate an image of a cocodrile",
      }),
    });

    return response;
  } catch (error) {
    console.error("Error generating image:", error);
  }
};
</script>
