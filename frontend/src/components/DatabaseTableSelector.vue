<template>
  <div class="database-selector">
    <h1 class="title">Seleccionar Tabla</h1>

    <div v-if="loading" class="message">Cargando tablas...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>
    <div v-else>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Buscar tablas..."
        class="search-input"
      />

      <div v-if="filteredTables.length === 0" class="message">
        No se encontraron tablas.
      </div>

      <div v-else class="tables-grid">
        <div
          v-for="table in filteredTables"
          :key="table.id"
          @click="selectTable(table)"
          class="table-card"
          :class="{ selected: selectedTable?.id === table.id }"
        >
          <h3 class="table-name">{{ table.name }}</h3>
          <p class="table-records">{{ table.recordCount }} registros</p>
        </div>
      </div>

      <div class="actions">
        <button
          @click="confirmSelection"
          :disabled="!selectedTable"
          class="action-button"
        >
          Seleccionar
        </button>
        <router-link
          :to="{ path: '/prompt', query: { table: selectedTable?.name } }"
          class="action-button"
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

const tables = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedTable = ref(null);
const searchQuery = ref("");

const filteredTables = computed(() => {
  if (!searchQuery.value) return tables.value;
  return tables.value.filter((table) =>
    table.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const fetchTables = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await fetch("http://127.0.0.1:8000/api/table_names");
    const data = await response.json();
    tables.value = (data.table_names || []).map((name, index) => ({
      id: index + 1,
      name,
      recordCount: Math.floor(Math.random() * 10000),
    }));
  } catch {
    error.value = "Error al cargar las tablas.";
  } finally {
    loading.value = false;
  }
};

const selectTable = (table) => {
  selectedTable.value = table;
};

const confirmSelection = () => {
  if (selectedTable.value)
    alert(`Tabla seleccionada: ${selectedTable.value.name}`);
};

onMounted(fetchTables);
</script>

<style scoped>
.database-selector {
  padding: 30px;
  max-width: 600px;
  margin: auto;
  text-align: center;
  background-color: #f9f9f9;
  border-radius: 10px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 26px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.message {
  font-size: 16px;
  color: #555;
}

.error {
  color: #d9534f;
}

.search-input {
  width: 100%;
  padding: 12px 20px;
  font-size: 16px;
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-sizing: border-box;
  background-color: #fff;
  transition: border-color 0.3s ease;
}

.search-input:focus {
  border-color: #007bff;
  outline: none;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.table-card {
  padding: 20px;
  background-color: #ffffff;
  border-radius: 8px;
  border: 1px solid #ddd;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.table-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.table-card.selected {
  background-color: #eef7ff;
  border-color: #007bff;
}

.table-name {
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.table-records {
  font-size: 14px;
  color: #777;
  margin-top: 5px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.action-button {
  padding: 12px 18px;
  font-size: 16px;
  border: none;
  border-radius: 8px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.action-button:hover {
  background-color: #0056b3;
  transform: translateY(-3px);
}

.action-button.disabled {
  background-color: #d6d6d6;
  cursor: not-allowed;
}

.action-button:focus {
  outline: none;
}
</style>
