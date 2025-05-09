<template>
  <div :class="['appContainer', isDarkMode ? 'dark-mode' : 'light-mode']">
    <!-- Barra lateral con clases dinámicas -->
    <div :class="['sidebar', { 'sidebar-closed': !isSidebarOpen }]">
      <div class="sidebarHeader">
        <h2>Chat History</h2>
        <button class="newChatButton" @click="createConversation(2)">
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
              ref="imageInput"
              @change="handleImageUpload"
              accept="image/*"
              multiple
            />
            <button
              type="button"
              class="custom-file-upload"
              @click="$refs.imageInput.click()"
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
const MAX_IMAGE_SIZE_MB = 1;
const MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024;
import { ref, nextTick, onMounted, onUnmounted } from "vue";
import { watch } from "vue";
import "./PromptToGPT.css";

import "highlight.js/styles/atom-one-dark.css"; // Another popular theme
import hljs from "highlight.js/lib/core";
import css from "highlight.js/lib/languages/css";
import javascript from "highlight.js/lib/languages/javascript";
import python from "highlight.js/lib/languages/python";
import java from "highlight.js/lib/languages/java";
import csharp from "highlight.js/lib/languages/csharp";
import php from "highlight.js/lib/languages/php";
import ruby from "highlight.js/lib/languages/ruby";
import go from "highlight.js/lib/languages/go";
import kotlin from "highlight.js/lib/languages/kotlin";
import swift from "highlight.js/lib/languages/swift";
import typescript from "highlight.js/lib/languages/typescript";
import html from "highlight.js/lib/languages/xml"; // XML is used for HTML
import json from "highlight.js/lib/languages/json";
import bash from "highlight.js/lib/languages/bash";
import sql from "highlight.js/lib/languages/sql";
import { marked } from "marked";
hljs.registerLanguage("sql", sql);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("python", python);
hljs.registerLanguage("css", css);
hljs.registerLanguage("java", java);
hljs.registerLanguage("csharp", csharp);
hljs.registerLanguage("php", php);
hljs.registerLanguage("ruby", ruby);
hljs.registerLanguage("go", go);
hljs.registerLanguage("kotlin", kotlin);
hljs.registerLanguage("swift", swift);
hljs.registerLanguage("typescript", typescript);
hljs.registerLanguage("html", html);
hljs.registerLanguage("json", json);
hljs.registerLanguage("bash", bash);

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
const api = "http://10.121.124.133:8000";
//prod :(
//const api = "http://10.121.30.150:8000";
//home office :)
//const api = "http://127.0.0.1:8000";

onMounted(async () => {
  await getChats();
  document.addEventListener("paste", handlePaste);
  applyCodeHighlighting();
});

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

watch(messages, () => {
  nextTick(() => {
    setTimeout(() => {
      applyCodeHighlighting();
    }, 50);
  });
});

const applyCodeHighlighting = () => {
  const codeBlocks = document.querySelectorAll("pre code");
  codeBlocks.forEach((block) => {
    hljs.highlightElement(block);
  });
};

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
  };

  return iconMap[extension] || "📁";
};

const getFilesContainer = (msg) => {
  return `
    <div class="message-file-container">
      ${msg.files
        .map((file) => {
          const fileName = file.name || "File";
          const fileIcon = getFileIcon(fileName);
          return `
            <div class="message-file">
              <div class="message-file-icon">${fileIcon}</div>
              <div class="message-file-name">${fileName}</div>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
};

const getImageContainer = (msg) => {
  return `
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
};

const escapeHtml = (unsafe) => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

const formatCodeBlock = (text) => {
  if (!text) return "";

  const codeBlockRegex = /```(\w*)\n([\s\S]*?)\n```(?!\w)/g;
  // /^(\w+)?\n([\s\S]*?)^```$/gm;
  const formattedText = text.replace(
    codeBlockRegex,
    (match, language, code) => {
      return `<div class="code-block">
            <div class="code-header">
              <span class="code-language">${language || "code"}</span>
              <button class="copy-button" onclick="copyToClipboard(this)">Copy</button>
            </div>
            <pre><code class="${language || ""}">${code}</code></pre>
          </div>`;
    }
  );
  return formattedText;
};

const formatMessageText = (msg) => {
  if (!msg) return "";

  const hasImages = msg.images && msg.images.length > 0;
  const hasFiles = msg.files && msg.files.length > 0;
  let result = "";

  if (hasImages) {
    result += getImageContainer(msg);
  }

  if (hasFiles) {
    result += getFilesContainer(msg);
  }

  let textPart = formatCodeBlock(
    typeof msg === "string" ? msg : msg.text || ""
  );

  textPart = marked.parse(textPart);

  return result + textPart;
};

const handlePaste = (event) => {
  const items = event.clipboardData.items;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const file = item.getAsFile();
      const reader = new FileReader();

      const fileType = file.type.split("/")[1];
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
      throw new Error(`Error requesting conversation id: ${response.status}`);
    }

    const data = await response.json();
    messages.value = data.response.map((msg) => {
      const base64Match = msg.content.match(
        /data:image\/[a-zA-Z]+;base64,[^"'\s]+/
      );
      const urlMatch = msg.content.match(/'url':\s*'([^']+)'/);
      const directUrlMatch = msg.content.match(/https:\/\/[^\s"']*/);

      if (base64Match || urlMatch || directUrlMatch) {
        return {
          isUser: msg.role === "user",
          text: {
            text: urlMatch || directUrlMatch ? "" : msg.content,
            images: [
              {
                base64: base64Match ? base64Match[0] : null,
                url: urlMatch
                  ? urlMatch[1]
                  : directUrlMatch
                  ? directUrlMatch
                  : null,
              },
            ],
          },
        };
      } else {
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

const createConversation = async (model) => {
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
    if (file.size > MAX_IMAGE_SIZE_BYTES) {
      errorMessage.value = `La imagen supera el límite de 1 MB.`;
      setTimeout(() => (errorMessage.value = ""), 4000);
      return;
    }
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
  //Manage data to send
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
  //Clean vars
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
      data = await response.json();
      const imageUrl = data.response.imageUrl || data.response;
      messages.value.pop();

      const messageText = data.response.text || "Generated image:";

      const imageHtml = `
                <div>
                  <p>${messageText}</p>
                  <div class="message-image-container">
                    <img src="${imageUrl}" alt="Generated Image" class="message-image"/>

                  </div>
                </div>
              `;

      messages.value.push({
        text: imageHtml,
        isUser: false,
      });
    } else {
      response = await fetch(`${api}/api/query_database`, {
        method: "POST",
        body: formData,
      });
      messages.value.pop();

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      const botMessage = {
        text: "",
        isUser: false,
      };

      messages.value.push(botMessage);
      let assistant_response = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        assistant_response += chunk;

        messages.value[messages.value.length - 1].text = assistant_response;

        console.log("Recibido:", chunk);
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
    applyCodeHighlighting();

    await nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop =
          messagesContainer.value.scrollHeight;
      }
    });
  }
};

const handleModel = () => {
  if (modelUsing.value === 1) {
    modelUsing.value === 2;
  } else {
    modelUsing.value === 1;
  }
};

const generateImg = async (prompt) => {
  try {
    const response = await fetch(`${api}/api/generateImage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        username: String(selectedChatId.value),
      }),
    });

    return response;
  } catch (error) {
    console.error("Error generating image:", error);
  }
};

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
};
const showDeleteOption = (chat) => {
  deleteOption.value = deleteOption.value === chat ? null : chat;
};
const removeImage = (index) => {
  selectedImages.value.splice(index, 1);
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
const toggleChurn = () => {
  isChurn.value = !isChurn.value;
};

const cleanScreen = () => {
  messages.value = [];
};

const newLine = (event) => {
  event.preventDefault();
  userPrompt.value += "\n";
};
</script>
