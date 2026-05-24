<template>
  <div class="w-full">
    <!-- Filtro de categoría -->
    <div class="mb-8 flex gap-3 overflow-x-auto pb-2">
      <button
        v-for="category in categories"
        :key="category"
        @click="selectedCategory = category"
        :class="[
          'rounded-smooth px-5 py-2 font-semibold transition whitespace-nowrap',
          selectedCategory === category
            ? 'btn-primary shadow-lg'
            : 'bg-primary-light/40 text-gray-700 hover:bg-primary-light/60 border-2 border-primary/20',
        ]"
      >
        {{ category }}
      </button>
    </div>

    <!-- Productos -->
    <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="product in filteredProducts"
        :key="product.id"
        class="card"
      >
        <!-- Imagen del producto -->
        <div class="mb-4 h-40 rounded-smooth bg-gradient-to-br from-primary/30 via-accent/20 to-primary-light/40 flex items-center justify-center">
          <span class="text-5xl font-bold text-primary">{{ product.name.substring(0, 1) }}</span>
        </div>

        <!-- Info del producto -->
        <h3 class="font-bold text-gray-800 text-lg">{{ product.name }}</h3>
        <p class="mt-2 text-sm text-gray-600">{{ product.description }}</p>

        <!-- Precio -->
        <div class="mt-5 flex items-baseline justify-between">
          <span class="text-3xl font-bold text-primary">${{ product.price }}</span>
          <span v-if="product.stock > 0" class="badge badge-secondary">
            Stock: {{ product.stock }}
          </span>
          <span v-else class="badge badge-error">
            Agotado
          </span>
        </div>

        <!-- Botón de compra -->
        <button
          @click="addToCart(product)"
          :disabled="product.stock === 0"
          class="mt-6 w-full btn-primary"
        >
          {{ product.stock === 0 ? 'Agotado' : 'Agregar al Carrito' }}
        </button>
      </div>
    </div>

    <!-- Carrito flotante -->
    <div
      v-if="cart.length > 0"
      class="fixed bottom-6 right-6 rounded-smoother bg-white shadow-2xl border-2 border-primary card"
    >
      <div class="p-5">
        <div class="flex items-center justify-between mb-4">
          <h4 class="font-bold text-lg text-gray-800">Carrito</h4>
          <span class="badge badge-primary">{{ cart.length }}</span>
        </div>
        <div class="mt-3 max-h-48 overflow-y-auto space-y-2 text-sm">
          <div v-for="(item, index) in cart" :key="index" class="flex justify-between items-center p-2 bg-gray-50 rounded-lg">
            <span class="text-gray-700">{{ item.name }} <span class="font-semibold text-primary">x{{ item.quantity }}</span></span>
            <span class="font-bold text-primary">${{ (item.price * item.quantity).toFixed(2) }}</span>
          </div>
        </div>
        <div class="mt-4 border-t-2 border-primary/20 pt-4 font-bold text-lg text-gray-800 flex justify-between">
          <span>Total:</span>
          <span class="text-primary">${{ cartTotal.toFixed(2) }}</span>
        </div>
        <button
          @click="checkout"
          class="mt-4 w-full btn-primary"
        >
          Comprar Ahora
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const selectedCategory = ref('Bebidas');

const categories = ['Bebidas', 'Comida', 'Snacks'];

const products = ref([
  // Bebidas
  { id: 1, name: 'Agua', description: 'Botella de agua 500ml', category: 'Bebidas', price: 1.50, stock: 20, emoji: '💧' },
  { id: 2, name: 'Jugo Natural', description: 'Jugo naranja fresco', category: 'Bebidas', price: 3.50, stock: 15, emoji: '🧃' },
  { id: 3, name: 'Bebida Energética', description: 'Energizante 250ml', category: 'Bebidas', price: 2.50, stock: 25, emoji: '⚡' },
  { id: 4, name: 'Café', description: 'Café caliente', category: 'Bebidas', price: 2.00, stock: 30, emoji: '☕' },
  
  // Comida
  { id: 5, name: 'Sándwich Pollo', description: 'Sándwich con pollo a la plancha', category: 'Comida', price: 6.50, stock: 10, emoji: '🥪' },
  { id: 6, name: 'Ensalada Fresca', description: 'Ensalada variada', category: 'Comida', price: 5.50, stock: 8, emoji: '🥗' },
  { id: 7, name: 'Pasta', description: 'Pasta con salsa', category: 'Comida', price: 7.00, stock: 12, emoji: '🍝' },
  
  // Snacks
  { id: 8, name: 'Proteína Bar', description: 'Barrita de proteína', category: 'Snacks', price: 3.00, stock: 40, emoji: '🍫' },
  { id: 9, name: 'Granola', description: 'Porción de granola', category: 'Snacks', price: 2.50, stock: 20, emoji: '🥣' },
  { id: 10, name: 'Frutos Secos', description: 'Mix de frutos secos', category: 'Snacks', price: 4.00, stock: 15, emoji: '🥜' },
]);

const cart = ref([]);

const filteredProducts = computed(() => {
  return products.value.filter(p => p.category === selectedCategory.value);
});

const cartTotal = computed(() => {
  return cart.value.reduce((total, item) => total + (item.price * item.quantity), 0);
});

const addToCart = (product) => {
  const existingItem = cart.value.find(item => item.id === product.id);
  if (existingItem) {
    existingItem.quantity++;
  } else {
    cart.value.push({
      ...product,
      quantity: 1,
    });
  }
};

const checkout = () => {
  alert(`Compra realizada! Total: $${cartTotal.value.toFixed(2)}`);
  cart.value = [];
};
</script>
