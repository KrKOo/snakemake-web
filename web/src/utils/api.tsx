import axios from 'axios';

console.log(import.meta.env.VITE_API_URL);

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 1000,
});

export default api;
