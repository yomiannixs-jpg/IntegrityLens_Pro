import axios from "axios"; export const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL || "https://integritylens-pro.onrender.com", timeout:180000});
