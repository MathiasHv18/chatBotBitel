<template>
  <div class="prompt-container">
    <h1 class="title">
      Consulta a ChatGPT sobre la tabla:
      <span v-if="selectedTable">{{ selectedTable }}</span>
      <span v-else class="warning">Selecciona una tabla</span>
    </h1>

    <textarea
      v-model="userPrompt"
      placeholder="Escribe tu consulta..."
      class="prompt-input"
      rows="4"
    ></textarea>

    <button
      @click="sendPrompt"
      :disabled="loading || !userPrompt || !selectedTable"
      class="send-button"
    >
      {{ loading ? "Consultando..." : "Enviar" }}
    </button>

    <div v-if="gptResponse" class="response-box">
      <h3>Respuesta de ChatGPT:</h3>
      <p>{{ gptResponse }}</p>
    </div>

    <div v-if="error" class="error-message">
      <p>Error: {{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const selectedTable = computed(() => route.query.table || "");

const userPrompt = ref("");
const gptResponse = ref(null);
const loading = ref(false);
const error = ref(null);

const sendPrompt = async () => {
  if (!selectedTable.value) {
    error.value = "No hay tabla seleccionada.";
    return;
  }

  loading.value = true;
  error.value = null;
  gptResponse.value = null;

  try {
    const response = await fetch("http://localhost:8000/api/query_table", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        table_name: selectedTable.value,
        prompt: userPrompt.value,
      }),
    });

    const data = await response.json();
    if (!response.ok || data.error) {
      throw new Error(data.error || "Error desconocido en el servidor.");
    }

    gptResponse.value = data.response;
  } catch (err) {
    error.value = err.message || "Error al comunicarse con el servidor.";
    console.error(err);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.prompt-container {
  max-width: 600px;
  margin: auto;
  padding: 20px;
  text-align: center;
}

.title {
  font-size: 22px;
  margin-bottom: 15px;
}

.warning {
  color: red;
  font-weight: bold;
}

.prompt-input {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  margin-bottom: 15px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.send-button {
  padding: 12px 20px;
  font-size: 16px;
  border: none;
  border-radius: 6px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
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
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
  text-align: left;
}

.error-message {
  margin-top: 15px;
  color: red;
  font-weight: bold;
}
</style>
