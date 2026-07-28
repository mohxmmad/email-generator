const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = (configuredBaseUrl || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function generateEmail(payload) {
  const response = await fetch(`${API_BASE_URL}/api/generate-email/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Failed to generate email.");
  }
  return data;
}
