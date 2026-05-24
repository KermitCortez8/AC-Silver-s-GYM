<template>
  <div class="space-y-8">
    <!-- Encabezado -->
    <section class="rounded-smoother border-2 border-primary/30 bg-gradient-to-r from-primary/15 via-accent/10 to-primary-light/20 p-8 shadow-lg">
      <p class="text-sm uppercase tracking-widest text-primary font-semibold">Gestión</p>
      <h1 class="mt-3 text-4xl font-bold bg-gradient-to-r from-primary to-primary-dark bg-clip-text text-transparent">Inventario</h1>
      <p class="mt-3 text-gray-700 font-medium">Controla máquinas, tienda y stock de tu gimnasio</p>
    </section>

    <!-- Pestañas -->
    <div class="flex gap-3 border-b-2 border-primary/20 overflow-x-auto pb-0">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        :class="[
          'px-5 py-3 font-semibold transition whitespace-nowrap border-b-2 text-base',
          activeTab === tab
            ? 'border-primary text-primary'
            : 'border-transparent text-gray-600 hover:text-primary',
        ]"
      >
        {{ tab }}
      </button>
    </div>

    <!-- Contenido según la pestaña -->
    <div class="space-y-8">
      <!-- Pestaña: Máquinas -->
      <div v-if="activeTab === 'Máquinas'" class="grid gap-6 lg:grid-cols-[1.2fr_1.8fr]">
        <!-- Formulario para agregar máquina -->
        <form
          @submit.prevent="handleSubmitMachine"
          class="rounded-smoother border-2 border-primary/20 bg-white p-6 h-fit card shadow-lg"
        >
          <h2 class="text-xl font-bold text-gray-800">{{ editingMachineId ? 'Editar Máquina' : 'Agregar Máquina' }}</h2>
          
          <div class="mt-6 space-y-4">
            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Nombre</span>
              <input
                v-model="machineForm.name"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
                placeholder="Ej: Cinta de correr"
              />
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Ubicación</span>
              <input
                v-model="machineForm.location"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
                placeholder="Ej: Zona A"
              />
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Estado</span>
              <select
                v-model="machineForm.status"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
              >
                <option>Operativa</option>
                <option>En mantenimiento</option>
                <option>Fuera de servicio</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Observaciones</span>
              <textarea
                v-model="machineForm.observations"
                rows="3"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
                placeholder="Detalles del mantenimiento o estado..."
              ></textarea>
            </label>
          </div>

          <button
            type="submit"
            class="mt-6 w-full btn-primary"
          >
            {{ editingMachineId ? 'Guardar cambios' : 'Agregar máquina' }}
          </button>

          <button
            v-if="editingMachineId"
            type="button"
            @click="resetMachineForm"
            class="mt-3 w-full btn-secondary"
          >
            Cancelar
          </button>
        </form>

        <!-- Lista de máquinas -->
        <div class="rounded-smoother border-2 border-primary/20 bg-white p-6 card">
          <h2 class="text-xl font-bold text-gray-800">Máquinas ({{ machines.length }})</h2>

          <div class="mt-6 space-y-4">
            <div
              v-for="machine in machines"
              :key="machine.id"
              :class="[
                'rounded-smooth border-2 p-5 hover:shadow-lg transition',
                machine.status === 'Operativa'
                  ? 'border-success/30 bg-gradient-to-br from-success/15 to-success/5'
                  : 'border-error/30 bg-gradient-to-br from-error/15 to-error/5',
              ]"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1">
                  <h3 class="font-bold text-lg text-gray-800">{{ machine.name }}</h3>
                  <p class="text-sm text-gray-600 mt-1">📍 {{ machine.location }}</p>
                  <div class="flex items-center gap-2 mt-3">
                    <span :class="['badge', machine.status === 'Operativa' ? 'badge-success' : 'badge-error']">
                      {{ machine.status }}
                    </span>
                  </div>
                  <p v-if="machine.observations" class="text-xs text-gray-600 mt-3 italic">{{ machine.observations }}</p>
                </div>

                <div class="flex gap-2">
                  <button
                    @click="editMachine(machine)"
                    class="rounded-smooth bg-primary/20 px-3 py-2 text-xs font-bold text-primary transition hover:bg-primary/30"
                  >
                    Editar
                  </button>
                  <button
                    @click="deleteMachine(machine.id)"
                    class="rounded-smooth bg-error/20 px-3 py-2 text-xs font-bold text-error transition hover:bg-error/30"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="machines.length === 0" class="mt-8 text-center">
            <p class="text-gray-500 text-lg">No hay máquinas registradas</p>
          </div>
        </div>
      </div>

      <!-- Pestaña: Tienda -->
      <div v-if="activeTab === 'Tienda'" class="grid gap-6 lg:grid-cols-[1.2fr_1.8fr]">
        <!-- Formulario para agregar producto -->
        <form
          @submit.prevent="handleSubmitProduct"
          class="rounded-smoother border-2 border-primary/20 bg-white p-6 h-fit card shadow-lg"
        >
          <h2 class="text-xl font-bold text-gray-800">{{ editingProductId ? 'Editar Producto' : 'Agregar Producto' }}</h2>
          
          <div class="mt-6 space-y-4">
            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Nombre</span>
              <input
                v-model="productForm.name"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
                placeholder="Ej: Proteína Bar"
              />
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Categoría</span>
              <select
                v-model="productForm.category"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
              >
                <option>Bebidas</option>
                <option>Comida</option>
                <option>Snacks</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Stock actual</span>
              <input
                v-model.number="productForm.stock"
                type="number"
                min="0"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
              />
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Stock mínimo</span>
              <input
                v-model.number="productForm.minStock"
                type="number"
                min="0"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
              />
            </label>

            <label class="space-y-2">
              <span class="text-sm font-semibold text-gray-700">Precio</span>
              <input
                v-model.number="productForm.price"
                type="number"
                step="0.01"
                min="0"
                class="w-full rounded-smooth border-2 border-primary/20 px-4 py-2 focus:border-primary focus:outline-none"
              />
            </label>
          </div>

          <button
            type="submit"
            class="mt-6 w-full btn-primary"
          >
            {{ editingProductId ? 'Guardar cambios' : 'Agregar producto' }}
          </button>

          <button
            v-if="editingProductId"
            type="button"
            @click="resetProductForm"
            class="mt-3 w-full btn-secondary"
          >
            Cancelar
          </button>
        </form>

        <!-- Lista de productos -->
        <div class="rounded-smoother border-2 border-primary/20 bg-white p-6 card">
          <h2 class="text-xl font-bold text-gray-800">Stock de Tienda ({{ storeProducts.length }})</h2>

          <div class="mt-6 space-y-4">
            <div
              v-for="product in storeProducts"
              :key="product.id"
              :class="[
                'rounded-smooth border-2 p-5 hover:shadow-lg transition',
                product.stock > product.minStock
                  ? 'border-success/30 bg-gradient-to-br from-success/15 to-success/5'
                  : 'border-warning/30 bg-gradient-to-br from-warning/15 to-warning/5',
              ]"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <h3 class="font-bold text-lg text-gray-800">{{ product.name }}</h3>
                    <span class="badge badge-secondary">{{ product.category }}</span>
                  </div>
                  <p class="text-lg font-bold text-primary mt-2">${{ product.price }}</p>
                  <div class="flex gap-4 mt-3 text-sm">
                    <span :class="['font-semibold', product.stock > product.minStock ? 'text-success' : 'text-warning']">
                      Stock: {{ product.stock }}
                    </span>
                    <span class="text-gray-600">Mín: {{ product.minStock }}</span>
                  </div>
                </div>

                <div class="flex gap-2">
                  <button
                    @click="editProduct(product)"
                    class="rounded-smooth bg-primary/20 px-3 py-2 text-xs font-bold text-primary transition hover:bg-primary/30"
                  >
                    Editar
                  </button>
                  <button
                    @click="deleteProduct(product.id)"
                    class="rounded-smooth bg-error/20 px-3 py-2 text-xs font-bold text-error transition hover:bg-error/30"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="storeProducts.length === 0" class="mt-8 text-center">
            <p class="text-gray-500 text-lg">No hay productos en la tienda</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';

const activeTab = ref('Máquinas');
const tabs = ['Máquinas', 'Tienda'];

// Estado para máquinas
const machines = ref([
  { id: 1, name: 'Cinta de correr 1', location: 'Zona A', status: 'Operativa', observations: 'En buen estado' },
  { id: 2, name: 'Cinta de correr 2', location: 'Zona A', status: 'Operativa', observations: '' },
  { id: 3, name: 'Bicicleta estática 1', location: 'Zona B', status: 'En mantenimiento', observations: 'Mantenimiento preventivo' },
]);

const machineForm = reactive({
  name: '',
  location: '',
  status: 'Operativa',
  observations: '',
});

const editingMachineId = ref(null);

const resetMachineForm = () => {
  editingMachineId.value = null;
  machineForm.name = '';
  machineForm.location = '';
  machineForm.status = 'Operativa';
  machineForm.observations = '';
};

const editMachine = (machine) => {
  editingMachineId.value = machine.id;
  machineForm.name = machine.name;
  machineForm.location = machine.location;
  machineForm.status = machine.status;
  machineForm.observations = machine.observations;
};

const handleSubmitMachine = () => {
  if (editingMachineId.value) {
    const index = machines.value.findIndex(m => m.id === editingMachineId.value);
    if (index !== -1) {
      machines.value[index] = { ...machines.value[index], ...machineForm };
    }
  } else {
    machines.value.push({
      id: Math.max(...machines.value.map(m => m.id), 0) + 1,
      ...machineForm,
    });
  }
  resetMachineForm();
};

const deleteMachine = (id) => {
  machines.value = machines.value.filter(m => m.id !== id);
};

// Estado para productos de tienda
const storeProducts = ref([
  { id: 1, name: 'Agua 500ml', category: 'Bebidas', stock: 20, minStock: 5, price: 1.50 },
  { id: 2, name: 'Jugo Natural', category: 'Bebidas', stock: 3, minStock: 10, price: 3.50 },
  { id: 3, name: 'Proteína Bar', category: 'Snacks', stock: 45, minStock: 15, price: 3.00 },
]);

const productForm = reactive({
  name: '',
  category: 'Bebidas',
  stock: 0,
  minStock: 0,
  price: 0,
});

const editingProductId = ref(null);

const resetProductForm = () => {
  editingProductId.value = null;
  productForm.name = '';
  productForm.category = 'Bebidas';
  productForm.stock = 0;
  productForm.minStock = 0;
  productForm.price = 0;
};

const editProduct = (product) => {
  editingProductId.value = product.id;
  productForm.name = product.name;
  productForm.category = product.category;
  productForm.stock = product.stock;
  productForm.minStock = product.minStock;
  productForm.price = product.price;
};

const handleSubmitProduct = () => {
  if (editingProductId.value) {
    const index = storeProducts.value.findIndex(p => p.id === editingProductId.value);
    if (index !== -1) {
      storeProducts.value[index] = { ...storeProducts.value[index], ...productForm };
    }
  } else {
    storeProducts.value.push({
      id: Math.max(...storeProducts.value.map(p => p.id), 0) + 1,
      ...productForm,
    });
  }
  resetProductForm();
};

const deleteProduct = (id) => {
  storeProducts.value = storeProducts.value.filter(p => p.id !== id);
};
</script>
