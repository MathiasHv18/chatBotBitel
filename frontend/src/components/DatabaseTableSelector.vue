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
    // In a real application, this would be an API call
    // Simulating API call with timeout
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Mock data
    tables.value = [
      { id: 1, name: "usuarios", recordCount: 1250 },
      { id: 2, name: "productos", recordCount: 5432 },
      { id: 3, name: "pedidos", recordCount: 8765 },
      { id: 4, name: "categorias", recordCount: 42 },
      { id: 5, name: "clientes", recordCount: 3201 },
      { id: 6, name: "proveedores", recordCount: 187 },
      { id: 7, name: "inventario", recordCount: 9543 },
      { id: 8, name: "transacciones", recordCount: 12500 },
      { id: 9, name: "empleados", recordCount: 310 },
    ];
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
  padding: 1.5rem;
  max-width: 72rem;
  margin-left: auto;
  margin-right: auto;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
  margin-bottom: 2rem;
}

.loading-spinner {
  animation: spin 1s linear infinite;
  border-radius: 9999px;
  height: 3rem;
  width: 3rem;
  border-bottom-width: 2px;
  border-color: #1a202c;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  background-color: #fed7d7;
  border: 1px solid #f56565;
  color: #c53030;
  padding: 0.75rem 1rem;
  border-radius: 0.25rem;
  margin-bottom: 1rem;
}

.search-container {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
}

.search-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.5);
}

.empty-message {
  text-align: center;
  padding: 2rem 0;
  color: #718096;
}

.tables-grid {
  display: grid;
  gap: 1rem;
}

@media (min-width: 768px) {
  .tables-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .tables-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.table-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.table-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.table-card.selected {
  background-color: #ebf8ff;
  border-color: #4299e1;
}

.table-content {
  display: flex;
  align-items: center;
}

.table-icon {
  margin-right: 0.75rem;
  color: #3182ce;
}

.table-name {
  font-weight: 500;
}

.table-records {
  font-size: 0.875rem;
  color: #718096;
}

.actions-container {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
}

.select-button {
  padding: 0.5rem 1.5rem;
  background-color: #3182ce;
  color: white;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.select-button:hover:not(.disabled) {
  background-color: #2c5282;
}

.select-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
