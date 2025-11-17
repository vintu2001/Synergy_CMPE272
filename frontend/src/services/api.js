import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function classifyMessage(residentId, messageText, options = {}) {
  // Make API call with optional abort signal
  const { data } = await apiClient.post("/api/v1/classify", {
    resident_id: residentId,
    message_text: messageText,
  }, {
    signal: options.signal, // Axios supports AbortController
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

export async function selectOption(requestId, selectedOptionId) {
  const { data } = await apiClient.post("/api/v1/select-option", {
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
  
  const { data } = await apiClient.post("/api/v1/resolve-request", payload);
  return data;
}

export async function updateRequestStatus(requestId, status, adminComment = null) {
  const payload = {
    request_id: requestId,
    status, // must match backend enum values: "Submitted", "Processing", "In Progress", "Resolved", "Escalated"
  };

  if (adminComment && adminComment.trim() !== "") {
    payload.admin_comment = adminComment.trim();
  }

  const { data } = await apiClient.post("/api/v1/update-status", payload);
  return data;
}
