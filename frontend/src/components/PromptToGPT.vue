<template>
  <div class="prompt-container">
    <h1 class="title">
      Consulta a ChatGPT sobre la tabla: {{ selectedTable.name }}
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

const props = defineProps({
  selectedTable: Object, // Recibe la tabla seleccionada
});

const userPrompt = ref("");
const gptResponse = ref(null);
const loading = ref(false);
const error = ref(null);

const sendPrompt = async () => {
  if (!props.selectedTable) return;

  loading.value = true;
  error.value = null;
  gptResponse.value = null;

  try {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userPrompt.value,
        table: props.selectedTable.name, // Enviar el nombre de la tabla al backend
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
  padding: 1.5rem;
  max-width: 48rem;
  margin-left: auto;
  margin-right: auto;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.prompt-input {
  width: 100%;
  height: 6rem;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  resize: none;
}

.send-button {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  background-color: #3182ce;
  color: white;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.send-button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.response-box {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #edf2f7;
  border-radius: 0.5rem;
}

.error-message {
  color: #e53e3e;
  margin-top: 1rem;
}
</style>
