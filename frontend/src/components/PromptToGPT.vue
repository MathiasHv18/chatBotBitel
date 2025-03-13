<template>
  <div class="prompt-container">
    <h1 class="title">
      Consulta a ChatGPT sobre la tabla: {{ selectedTable }}
    </h1>

    <textarea
      v-model="userPrompt"
      placeholder="Escribe tu consulta..."
      class="prompt-input"
    ></textarea>

    <button
      @click="sendPrompt"
      :disabled="loading || !userPrompt"
      class="send-button"
    >
      {{ loading ? "Consultando..." : "Enviar" }}
    </button>

    <div v-if="gptResponse" class="response-box">
      <h3>Respuesta de ChatGPT:</h3>
      <p>{{ gptResponse }}</p>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const selectedTable = route.query.table;

const userPrompt = ref("");
const gptResponse = ref(null);
const loading = ref(false);
const error = ref(null);

const sendPrompt = async () => {
  if (!selectedTable) return;

  loading.value = true;
  error.value = null;
  gptResponse.value = null;

  try {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userPrompt.value,
        table: selectedTable, // Enviar el nombre de la tabla al backend
      }),
    });

    const data = await response.json();
    gptResponse.value = data.response;
  } catch (err) {
    error.value = "Error al comunicarse con ChatGPT. Inténtelo nuevamente.";
    console.error(err);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.prompt-container {
  padding: 20px;
}

.title {
  font-size: 24px;
  margin-bottom: 20px;
}

.prompt-input {
  width: 100%;
  height: 100px;
  padding: 10px;
  font-size: 16px;
  margin-bottom: 20px;
}

.send-button {
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
  border: none;
  border-radius: 4px;
  background-color: #007bff;
  color: white;
  transition: background-color 0.3s;
}

.send-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.send-button:not(:disabled):hover {
  background-color: #0056b3;
}

.response-box {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.error-message {
  margin-top: 20px;
  color: red;
}
</style>
