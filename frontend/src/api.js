import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://integritylens-pro.onrender.com";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
});

export async function analyzeDocument({ file, text, searchWeb, excludeBibliography }) {
  const form = new FormData();
  if (file) form.append("file", file);
  if (text?.trim()) form.append("text", text.trim());
  form.append("search_web", String(searchWeb));
  form.append("exclude_bibliography", String(excludeBibliography));

  // Compatibility cascade for existing IntegrityLens backend versions.
  const endpoints = ["/api/analyze", "/api/analyze-document", "/analyze"];
  let lastError;
  for (const endpoint of endpoints) {
    try {
      const { data } = await api.post(endpoint, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    } catch (err) {
      lastError = err;
      if (err?.response?.status && ![404, 405, 422].includes(err.response.status)) throw err;
    }
  }
  throw lastError || new Error("Analysis endpoint unavailable.");
}
