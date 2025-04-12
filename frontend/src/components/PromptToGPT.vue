<template>
  <div :class="['appContainer', isDarkMode ? 'dark-mode' : 'light-mode']">
    <!-- Barra lateral con clases dinámicas -->
    <div :class="['sidebar', { 'sidebar-closed': !isSidebarOpen }]">
      <div class="sidebarHeader">
        <h2>Chat History</h2>
        <button class="newChatButton" @click="chooseModel(2)">
          + New Chat
        </button>
      </div>
      <ul>
        <li
          v-for="chat in [...chatHistory].reverse()"
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

    <div :class="['chatContainer', { 'chat-expanded': !isSidebarOpen }]">
      <div class="topBar">
        <button
          class="sidebar-toggle"
          @click="toggleSidebar"
          :class="{ 'sidebar-toggle-closed': !isSidebarOpen }"
        >
          {{ isSidebarOpen ? "◀" : "▶" }}
        </button>

        <button @click="toggleDarkMode" class="modeToggle">
          {{ isDarkMode ? "🌙 Dark Mode" : "☀️ Light Mode" }}
        </button>
        <select
          v-model="modelUsing"
          @change="handleModel"
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
          :class="{
            userMessage: msg.isUser,
            botMessage: !msg.isUser,
          }"
        >
          <span v-if="msg.isUser" v-html="formatMessageText(msg.text)"></span>
          <span
            v-else
            v-html="msg.isTyping ? msg.text : formatMessageText(msg.text)"
          ></span>
        </div>
      </div>
      <div class="inputContainer">
        <!-- Vista previa de imágenes (altura fija) -->
        <div v-if="selectedImages.length" class="imagePreviewContainer">
          <div
            v-for="(image, index) in selectedImages"
            :key="index"
            class="imagePreview"
          >
            <img :src="image.base64" alt="Preview" class="previewImage" />
            <button @click="removeImage(index)">✖</button>
          </div>
        </div>
        <div v-if="selectedFiles.length" class="filePreviewContainer">
          <div
            v-for="(file, index) in selectedFiles"
            :key="index"
            class="filePreview"
          >
            <div class="filePreviewIcon">
              {{ getFileIcon(file.name) }}
            </div>
            <div class="filePreviewName">{{ file.name }}</div>
            <button @click="removeFile(index)">✖</button>
          </div>
        </div>

        <!-- Área de texto (altura ajustable) -->
        <div class="userPromptContainer">
          <textarea
            v-model="userPrompt"
            placeholder="Ask anything"
            ref="textareaRef"
            @input="adjustTextareaHeight"
            @keydown.enter.exact.prevent="sendPrompt"
            @keydown.enter.shift.prevent="newLine"
          ></textarea>
        </div>

        <!-- Botones (altura fija) -->
        <div class="userInputFile">
          <button
            class="toggleGeneration"
            :class="{ active: isImageGeneration }"
            @click="handleImageGeneration"
          >
            Generate image
          </button>
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
            <!--Files-->
            <input
              type="file"
              ref="fileInput"
              @change="handleFileUpload"
              accept=".pdf,.xls,.xlsx,.csv,.doc,.docx,.txt"
              multiple
            />
            <button
              type="button"
              class="custom-file-upload"
              @click="$refs.fileInput.click()"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                class="clip-icon"
                style="width: 24px; height: 24px"
              >
                <path
                  d="M21.586 10.461l-10.05 10.05c-1.95 1.95-5.123 1.95-7.071 0-1.95-1.95-1.95-5.122 0-7.072l9.344-9.344c1.17-1.17 3.073-1.17 4.242 0 1.172 1.17 1.172 3.072 0 4.242l-8.637 8.637c-.39.39-1.023.39-1.414 0-.39-.39-.39-1.023 0-1.414l7.072-7.072"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  stroke="currentColor"
                  fill="none"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="errorNotification" v-if="errorMessage">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from "vue";
import { watch } from "vue";

import "./PromptToGPT.css";

const messagesContainer = ref(null);
const selectedImages = ref([]);
const selectedFiles = ref([]);
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
const isImageGeneration = ref(false);
const isSidebarOpen = ref(true);

//office pc
//const api = "http://192.168.137.1:8000";
//prod :(
const api = "http://10.121.30.150:8000";
//home office :)
//const api = "http://127.0.0.1:8000";

const getFileIcon = (filename) => {
  const extension = filename.split(".").pop().toLowerCase();

  const iconMap = {
    pdf: "📄",
    doc: "📝",
    docx: "📝",
    xls: "📊",
    xlsx: "📊",
    csv: "📊",
    txt: "📝",
    // Add more mappings as needed
  };

  return iconMap[extension] || "📁";
};
const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
};

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
};

const handleImageGeneration = () => {
  isImageGeneration.value = !isImageGeneration.value;
};

onMounted(async () => {
  await chooseModel(2);
  await getChats();
  document.addEventListener("paste", handlePaste);
});

const formatMessageText = (msg) => {
  if (!msg) return "";

  if (
    msg.images &&
    msg.images.length > 0 &&
    msg.files &&
    msg.files.length > 0
  ) {
    const imagesHtml = `
      <div class="message-image-container">
        ${msg.images
          .map((image) => {
            const imageSource = image.base64 || image.url;
            return imageSource
              ? `<img src="${imageSource}" alt="Message Image" class="message-image"/>`
              : "";
          })
          .join("")}
      </div>
    `;

    const filesHtml = `
      <div class="message-file-container">
        ${msg.files
          .map((file) => {
            const fileName = file.name || "File";
            const fileSize = formatFileSize(file.size);
            const fileIcon = getFileIcon(fileName);

            return `
              <div class="message-file">
                <div class="message-file-icon">${fileIcon}</div>
                <div class="message-file-name">${fileName}</div>
                ${
                  fileSize
                    ? `<div class="message-file-size">${fileSize}</div>`
                    : ""
                }
              </div>
            `;
          })
          .join("")}
      </div>
    `;

    // Texto asociado con los archivos
    const textPart = msg.text && msg.text.trim() ? formatMessage(msg.text) : "";
    return `${imagesHtml}${filesHtml}${textPart}`;
  }

  // Para mensajes con imágenes
  if (msg.images && msg.images.length > 0) {
    const imagesHtml = `
      <div class="message-image-container">
        ${msg.images
          .map((image) => {
            const imageSource = image.base64 || image.url;
            return imageSource
              ? `<img src="${imageSource}" alt="Message Image" class="message-image"/>`
              : "";
          })
          .join("")}
      </div>
    `;

    // Texto asociado con las imágenes
    const textPart = msg.text && msg.text.trim() ? formatMessage(msg.text) : "";
    return `${imagesHtml}${textPart}`;
  }

  // Para mensajes con archivos
  if (msg.files && msg.files.length > 0) {
    const filesHtml = `
      <div class="message-file-container">
        ${msg.files
          .map((file) => {
            const fileName = file.name || "File";
            const fileSize = formatFileSize(file.size);
            const fileIcon = getFileIcon(fileName);

            return `
              <div class="message-file">
                <div class="message-file-icon">${fileIcon}</div>
                <div class="message-file-name">${fileName}</div>
                ${
                  fileSize
                    ? `<div class="message-file-size">${fileSize}</div>`
                    : ""
                }
              </div>
            `;
          })
          .join("")}
      </div>
    `;

    // Texto asociado con los archivos
    const textPart = msg.text && msg.text.trim() ? formatMessage(msg.text) : "";
    return `${filesHtml}${textPart}`;
  }

  // Para mensajes solo de texto (estructura original que funciona)
  return formatMessage(msg.text || msg);
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const handlePaste = (event) => {
  const items = event.clipboardData.items;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const file = item.getAsFile();
      const reader = new FileReader();

      // Generar un nombre único con la extensión correcta basada en el tipo MIME
      const fileType = file.type.split("/")[1]; // Obtener 'png', 'jpeg', etc.
      const timestamp = new Date().getTime();
      const uniqueFilename = `pasted-image-${timestamp}.${fileType}`;

      reader.onload = () => {
        selectedImages.value.push({
          filename: uniqueFilename,
          base64: reader.result,
        });
        nextTick(() => {
          adjustTextareaHeight();
        });
      };
      reader.readAsDataURL(file);
    }
  }
};

watch(
  selectedImages,
  () => {
    nextTick(() => {
      adjustTextareaHeight();
    });
  },
  { deep: true }
);

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
  }, 3000);
};

const adjustTextareaHeight = () => {
  const textarea = textareaRef.value;
  if (!textarea) return;

  textarea.style.height = "auto";

  const scrollHeight = textarea.scrollHeight;

  const maxHeight = 150;

  textarea.style.height = `${Math.min(scrollHeight, maxHeight)}px`;

  textarea.style.overflowY = scrollHeight > maxHeight ? "auto" : "hidden";
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
    messages.value = data.response.map((msg) => {
      // Detectar si el contenido tiene una imagen en base64
      const base64Match = msg.content.match(
        /data:image\/[a-zA-Z]+;base64,[^"'\s]+/
      );
      // Detectar si el contenido tiene una URL de imagen
      const urlMatch = msg.content.match(/'url':\s*'([^']+)'/);

      if (base64Match || urlMatch) {
        // Si encontramos una imagen (base64 o URL)
        return {
          isUser: msg.role === "user",
          text: {
            // Para mensajes con URL, no incluimos el texto original
            text: urlMatch ? "" : msg.content,
            images: [
              {
                base64: base64Match ? base64Match[0] : null,
                url: urlMatch ? urlMatch[1] : null,
              },
            ],
          },
        };
      } else {
        // Es un mensaje de texto normal
        return {
          text: msg.content,
          isUser: msg.role === "user",
        };
      }
    });

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

const handleFileUpload = (event) => {
  const files = event.target.files;
  if (!files.length) return;
  Array.from(files).forEach((file) => {
    selectedFiles.value.push(file);
  });

  console.log(selectedFiles.value);
  event.target.value = "";
};

const handleImageUpload = (event) => {
  const files = event.target.files;
  if (!files.length) return;

  Array.from(files).forEach((file) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      selectedImages.value.push({
        filename: file.name,
        base64: reader.result,
      });
      nextTick(() => {
        adjustTextareaHeight();
      });
    };
  });

  event.target.value = "";
};

const formatMessage = (text) => {
  if (!text) return "";

  const codeBlockRegex = /```([a-zA-Z]*)\n([\s\S]*?)```/g;

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

  return formattedText
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br>");
};

const escapeHtml = (unsafe) => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

window.copyToClipboard = (button) => {
  const codeBlock = button.closest(".code-block").querySelector("code");
  const text = codeBlock.textContent;

  const fallbackCopyTextToClipboard = (text) => {
    const textArea = document.createElement("textarea");
    textArea.value = text;

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

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        updateButtonState(button);
      })
      .catch(() => {
        fallbackCopyTextToClipboard(text);
        updateButtonState(button);
      });
  } else {
    fallbackCopyTextToClipboard(text);
    updateButtonState(button);
  }
};

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
  if (
    !userPrompt.value &&
    selectedImages.value.length === 0 &&
    selectedFiles.value.length === 0
  )
    return;

  //Get images if not empty
  const imagesToSend =
    selectedImages.value.length > 0 ? [...selectedImages.value] : [];
  //Get files if not empty
  const filesToSend =
    selectedFiles.value.length > 0 ? [...selectedFiles.value] : [];

  const formData = new FormData();

  formData.append("modelUser", modelUsing.value);
  formData.append("username", String(selectedChatId.value));
  formData.append("isChurn", isChurn.value);
  formData.append("images", JSON.stringify(imagesToSend));
  filesToSend.forEach((file, i) => formData.append("files", file));

  const promptText = userPrompt.value;
  formData.append("prompt", promptText);
  userPrompt.value = "";

  if (textareaRef.value) {
    adjustTextareaHeight();
  }

  messages.value.push({
    text: {
      text: promptText,
      images: imagesToSend,
      files: filesToSend,
    },
    isUser: true,
  });

  selectedImages.value = [];
  selectedFiles.value = [];

  const typingMessage = {
    text: '<div class="typing-indicator"><span></span><span></span><span></span></div>',
    isUser: false,
    isTyping: true,
  };
  messages.value.push(typingMessage);
  loading.value = true;

  await nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });

  try {
    let response = null;
    let data = null;

    if (isImageGeneration.value) {
      response = await generateImg(promptText);
    } else {
      response = await fetch(`${api}/api/query_database`, {
        method: "POST",
        body: formData,
      });
    }

    data = await response.json();

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
      if (isImageGeneration.value) {
        const imageUrl = data.response.imageUrl || data.response;
        const messageText = data.response.text || "Generated image:";

        const imageHtml = `
                <div>
                  <p>${messageText}</p>
                  <div class="message-image-container">
                    <img src="${imageUrl}" alt="Generated Image" class="message-image"/>
                    <a href="${imageUrl}" download="generated-image.png" class="download-button">
                      Descargar imagen
                    </a>
                  </div>
                </div>
              `;

        messages.value.push({
          text: imageHtml,
          isUser: false,
        });
      } else {
        console.log(data.response);
        messages.value.push({ text: data.response, isUser: false });
      }
    }
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

const generateImg = async (prompt) => {
  try {
    const response = await fetch(`${api}/api/generateImage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
      }),
    });

    return response;
  } catch (error) {
    console.error("Error generating image:", error);
  }
};

const handleModel = () => {
  if (modelUsing.value === 1) {
    modelUsing.value === 2;
  } else {
    modelUsing.value === 1;
  }
};
</script>
