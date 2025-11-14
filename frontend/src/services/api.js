import axios from "axios";

// API Gateway URL - update for production deployment
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function classifyMessage(residentId, messageText) {
  const { data } = await apiClient.post("/api/classify", {
    resident_id: residentId,
    message_text: messageText,
  });
  return data;
}

export async function getResidentRequests(residentId) {
  const { data } = await apiClient.get(`/api/requests/${encodeURIComponent(residentId)}`);
  return data;
}

export async function getAllRequests(adminApiKey) {
  const { data } = await apiClient.get("/api/admin/all-requests", {
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
  
  const { data } = await apiClient.post("/api/requests/submit", payload);
  return data;
}

export async function selectOption(requestId, selectedOptionId) {
  const { data } = await apiClient.post("/api/requests/select", {
    request_id: requestId,
    selected_option_id: selectedOptionId,
  });
  return data;
}

export async function resolveRequest(requestId, resolvedBy, resolutionNotes = null) {
  const payload = {
    request_id: requestId,
    resolved_by: resolvedBy,
  };
  if (resolutionNotes) payload.resolution_notes = resolutionNotes;
  
  const { data } = await apiClient.post("/api/requests/resolve", payload);
  return data;
}

export async function queryGovernanceLogs(query, adminApiKey) {
  const { data } = await apiClient.post("/api/governance/query", query, {
    headers: {
      "X-API-Key": adminApiKey,
    },
  });
  return data;
}

export async function getGovernanceStats(adminApiKey) {
  const { data } = await apiClient.get("/api/governance/stats", {
    headers: {
      "X-API-Key": adminApiKey,
    },
  });
  return data;
}

export async function exportGovernanceLogs(format, adminApiKey) {
  const { data } = await apiClient.get(`/api/governance/export?format=${format}`, {
    headers: {
      "X-API-Key": adminApiKey,
    },
  });
  return data;
}

