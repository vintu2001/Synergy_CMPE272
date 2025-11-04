import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function classifyMessage(residentId, messageText) {
  const { data } = await apiClient.post("/api/v1/classify", {
    resident_id: residentId,
    message_text: messageText,
  });
  return data;
}

export async function getResidentRequests(residentId) {
  const { data } = await apiClient.get(`/api/v1/get-requests/${encodeURIComponent(residentId)}`);
  return data;
}

export async function getAllRequests(adminApiKey) {
  const { data } = await apiClient.get("/api/v1/admin/all-requests", {
    headers: {
      "X-API-Key": adminApiKey,
    },
  });
  return data;
}

export async function submitRequest(residentId, messageText, category = null, urgency = null) {
  const payload = {
    resident_id: residentId,
    message_text: messageText,
  };
  if (category) payload.category = category;
  if (urgency) payload.urgency = urgency;
  
  const { data } = await apiClient.post("/api/v1/submit-request", payload);
  return data;
}


