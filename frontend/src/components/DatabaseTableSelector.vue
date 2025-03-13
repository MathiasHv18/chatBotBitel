<template>
  <div class="database-selector">
    <h1 class="title">Seleccionar Tabla de Base de Datos</h1>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
    </div>

    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div v-else>
      <div class="search-container">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar tablas..."
          class="search-input"
        />
      </div>

      <div v-if="filteredTables.length === 0" class="empty-message">
        No se encontraron tablas que coincidan con su búsqueda
      </div>

      <div v-else class="tables-grid">
        <div
          v-for="table in filteredTables"
          :key="table.id"
          @click="selectTable(table)"
          class="table-card"
          :class="{ selected: selectedTable?.id === table.id }"
        >
          <div class="table-content">
            <div class="table-icon">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="lucide lucide-database"
              >
                <ellipse cx="12" cy="5" rx="9" ry="3" />
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" />
              </svg>
            </div>
            <div>
              <h3 class="table-name">{{ table.name }}</h3>
              <p class="table-records">{{ table.recordCount }} registros</p>
            </div>
          </div>
        </div>
      </div>

      <div class="actions-container">
        <button
          @click="confirmSelection"
          class="select-button"
          :disabled="!selectedTable"
          :class="{ disabled: !selectedTable }"
        >
          Seleccionar Tabla
        </button>
        <router-link
          :to="{ path: '/prompt', query: { table: selectedTable?.name } }"
          class="select-button"
          :class="{ disabled: !selectedTable }"
        >
          Ir a Prompt
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";

// State
const tables = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedTable = ref(null);
const searchQuery = ref("");

// Computed properties
const filteredTables = computed(() => {
  if (!searchQuery.value) return tables.value;

  const query = searchQuery.value.toLowerCase();
  return tables.value.filter((table) =>
    table.name.toLowerCase().includes(query)
  );
});

// Methods
const fetchTables = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await fetch("http://127.0.0.1:8000/api/table_names");
    const data = await response.json();

    // Acceder a la propiedad table_names del objeto respuesta
    const tableNames = data.table_names || [];

    // Ahora mapea los nombres a objetos con id y recordCount
    tables.value = tableNames.map((name, index) => ({
      id: index + 1,
      name,
      recordCount: Math.floor(Math.random() * 10000), // Mock record count
    }));
  } catch (err) {
    error.value =
      "Error al cargar las tablas de la base de datos. Por favor, inténtelo de nuevo.";
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const selectTable = (table) => {
  selectedTable.value = table;
};

const confirmSelection = () => {
  if (selectedTable.value) {
    // In a real application, you would emit an event or use a router to navigate
    alert(`Tabla seleccionada: ${selectedTable.value.name}`);
  }
};

// Lifecycle hooks
onMounted(() => {
  fetchTables();
});
</script>

<style scoped>
.database-selector {
  padding: 20px;
}

.title {
  font-size: 24px;
  margin-bottom: 20px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #000;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: red;
}

.search-container {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px;
  font-size: 16px;
}

.empty-message {
  text-align: center;
  color: #888;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.table-card {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.table-card.selected {
  background-color: #f0f0f0;
}

.table-content {
  display: flex;
  align-items: center;
}

.table-icon {
  margin-right: 10px;
}

.table-name {
  font-size: 18px;
  margin: 0;
}

.table-records {
  color: #666;
}

.actions-container {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
}

.select-button {
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
  border: none;
  border-radius: 4px;
  background-color: #007bff;
  color: white;
  transition: background-color 0.3s;
}

.select-button.disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.select-button:not(.disabled):hover {
  background-color: #0056b3;
}
</style>
