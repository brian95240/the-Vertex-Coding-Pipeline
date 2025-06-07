import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import axios from 'axios';

// Configure Axios base URL (adjust if your API runs elsewhere)
axios.defaults.baseURL = 'http://localhost:8000/api'; // Assuming backend runs on port 8000

// Create Vue app instance
const app = createApp(App);

// Use Pinia for state management
app.use(createPinia());

// Use Vue Router for routing
app.use(router);

// Mount the app
app.mount('#app');

