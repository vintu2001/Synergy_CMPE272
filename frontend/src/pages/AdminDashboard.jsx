// frontend/src/pages/AdminDashboard.jsx
import React, { useEffect, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Filter,
  Loader2,
} from "lucide-react";

import {
  getAllRequests,
  resolveRequest,
  updateRequestStatus,
} from "../services/api";

function StatusBadge({ status }) {
  const base =
    "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold";
  const map = {
    Submitted: "bg-slate-100 text-slate-700",
    "In Progress": "bg-blue-100 text-blue-700",
    Processing: "bg-blue-100 text-blue-700",
    Resolved: "bg-emerald-100 text-emerald-700",
    Escalated: "bg-amber-100 text-amber-700",
    default: "bg-slate-100 text-slate-700",
  };

  const cls = map[status] || map.default;

  return <span className={`${base} ${cls}`}>{status}</span>;
}

export default function AdminDashboard() {
  const [items, setItems] = useState([]);
  const [expandedRow, setExpandedRow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [filterStatus, setFilterStatus] = useState("ALL");

  // For "Mark resolved" modal
  const [resolveModal, setResolveModal] = useState({
    open: false,
    requestId: null,
    requestText: "",
    notes: "",
  });

  // NEW: per-request status + comment edits
  const [statusEdits, setStatusEdits] = useState({}); // { [requestId]: { status, comment } }

  const load = async () => {
    try {
      setLoading(true);
      const data = await getAllRequests();
      setItems(Array.isArray(data) ? data : data?.items ?? []);
    } catch (e) {
      console.error(e);
      setToast({
        message: "Failed to load requests.",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filteredItems =
    filterStatus === "ALL"
      ? items
      : items.filter((r) => r.status === filterStatus);

  const handleResolve = async () => {
    if (!resolveModal.requestId) return;
    try {
      await resolveRequest(resolveModal.requestId, resolveModal.notes);
      setToast({ message: "Request marked as resolved.", type: "success" });
      setResolveModal({
        open: false,
        requestId: null,
        requestText: "",
        notes: "",
      });
      load();
    } catch (e) {
      console.error(e);
      setToast({
        message: "Failed to resolve request.",
        type: "error",
      });
    }
  };

  const handleStatusUpdate = async (requestId) => {
    const entry = statusEdits[requestId] || {};
    const currentRow = items.find((r) => r.request_id === requestId);
    const newStatus = entry.status || currentRow?.status;
    const comment = entry.comment || "";

    if (!newStatus) {
      setToast({
        message: "Please select a status before updating.",
        type: "error",
      });
      return;
    }

    try {
      await updateRequestStatus(requestId, newStatus, comment);
      setToast({
        message: "Status and comment updated.",
        type: "success",
      });

      setStatusEdits((prev) => {
        const copy = { ...prev };
        delete copy[requestId];
        return copy;
      });

      load();
    } catch (e) {
      console.error(e);
      setToast({
        message: "Failed to update status. Please try again.",
        type: "error",
      });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-6 text-slate-900 dark:bg-slate-950 dark:text-slate-50 sm:px-6 lg:px-8">
      {/* Header */}
      <header className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Admin Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Monitor and manage maintenance requests from residents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              className="bg-transparent text-sm outline-none"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="ALL">All statuses</option>
              <option value="Submitted">Submitted</option>
              <option value="Processing">Processing</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
              <option value="Escalated">Escalated</option>
            </select>
          </div>
          <button
            onClick={load}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-slate-100"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Refreshing…
              </>
            ) : (
              <>
                <Loader2 className="h-4 w-4" />
                Refresh
              </>
            )}
          </button>
        </div>
      </header>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-900/60">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                &nbsp;
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Request ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Message
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Urgency
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Risk
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white dark:divide-slate-800 dark:bg-slate-900">
            {filteredItems.length === 0 && !loading && (
              <tr>
                <td
                  colSpan={9}
                  className="px-6 py-10 text-center text-sm text-slate-500 dark:text-slate-400"
                >
                  No requests found.
                </td>
              </tr>
            )}

            {filteredItems.map((r) => (
              <React.Fragment key={r.request_id}>
                <tr className="hover:bg-slate-50/60 dark:hover:bg-slate-900/60">
                  {/* Expand toggle */}
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedRow((prev) =>
                          prev === r.request_id ? null : r.request_id
                        )
                      }
                      className="rounded-full border border-slate-200 p-1 text-slate-500 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
                    >
                      {expandedRow === r.request_id ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>
                  </td>

                  <td className="whitespace-nowrap px-6 py-3 text-xs font-mono text-slate-500 dark:text-slate-400">
                    {r.request_id}
                  </td>

                  <td className="max-w-xs px-6 py-3">
                    <p className="line-clamp-2 text-sm text-slate-800 dark:text-slate-100">
                      {r.message_text}
                    </p>
                  </td>

                  <td className="whitespace-nowrap px-6 py-3 text-sm text-slate-700 dark:text-slate-200">
                    {r.category}
                  </td>

                  <td className="whitespace-nowrap px-6 py-3 text-sm">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                        r.urgency === "High"
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300"
                          : r.urgency === "Medium"
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
                          : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                      }`}
                    >
                      {r.urgency}
                    </span>
                  </td>

                  <td className="whitespace-nowrap px-6 py-3">
                    <StatusBadge status={r.status} />
                  </td>

                  <td className="whitespace-nowrap px-6 py-3">
                    {typeof r.risk_forecast === "number" ? (
                      <div className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                        <AlertTriangle className="h-3 w-3" />
                        {Math.round(r.risk_forecast * 100)}%
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">N/A</span>
                    )}
                  </td>

                  <td className="whitespace-nowrap px-6 py-3 text-sm text-slate-700 dark:text-slate-200">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-slate-400" />
                      {r.created_at
                        ? new Date(r.created_at).toLocaleString()
                        : "-"}
                    </div>
                  </td>

                  <td className="whitespace-nowrap px-6 py-3 text-right">
                    {r.status !== "Resolved" && (
                      <button
                        type="button"
                        onClick={() =>
                          setResolveModal({
                            open: true,
                            requestId: r.request_id,
                            requestText: r.message_text,
                            notes: "",
                          })
                        }
                        className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-600 dark:bg-emerald-400 dark:text-emerald-950 dark:hover:bg-emerald-300"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Mark resolved
                      </button>
                    )}
                  </td>
                </tr>

                {/* Expanded row */}
                {expandedRow === r.request_id && (
                  <tr key={`${r.request_id}-details`}>
                    <td
                      colSpan={9}
                      className="bg-slate-50 px-6 py-6 dark:bg-slate-900/60"
                    >
                      <div className="grid gap-4 md:grid-cols-2">
                        {/* Resident message */}
                        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                            Resident message
                          </h4>
                          <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
                            {r.message_text}
                          </p>
                          <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-500 dark:text-slate-400">
                            <div>
                              <dt className="font-semibold">Category</dt>
                              <dd>{r.category}</dd>
                            </div>
                            <div>
                              <dt className="font-semibold">Urgency</dt>
                              <dd>{r.urgency}</dd>
                            </div>
                            <div>
                              <dt className="font-semibold">Status</dt>
                              <dd>{r.status}</dd>
                            </div>
                            {r.risk_forecast != null && (
                              <div>
                                <dt className="font-semibold">Risk forecast</dt>
                                <dd>{Math.round(r.risk_forecast * 100)}%</dd>
                              </div>
                            )}
                          </dl>
                        </div>

                        {/* Admin controls: status + comment */}
                        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                            Admin controls
                          </h4>

                          <div className="mt-3 space-y-3">
                            <div>
                              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                Status
                              </label>
                              <select
                                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                                value={
                                  statusEdits[r.request_id]?.status ?? r.status
                                }
                                onChange={(e) =>
                                  setStatusEdits((prev) => ({
                                    ...prev,
                                    [r.request_id]: {
                                      ...(prev[r.request_id] || {}),
                                      status: e.target.value,
                                    },
                                  }))
                                }
                              >
                                {[
                                  "Submitted",
                                  "Processing",
                                  "In Progress",
                                  "Resolved",
                                  "Escalated",
                                ].map((s) => (
                                  <option key={s} value={s}>
                                    {s}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div>
                              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                Admin comment (visible to resident)
                              </label>
                              <textarea
                                rows={3}
                                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                                placeholder="Add a brief note for the resident..."
                                value={
                                  statusEdits[r.request_id]?.comment ??
                                  r.admin_comment ??
                                  ""
                                }
                                onChange={(e) =>
                                  setStatusEdits((prev) => ({
                                    ...prev,
                                    [r.request_id]: {
                                      ...(prev[r.request_id] || {}),
                                      comment: e.target.value,
                                    },
                                  }))
                                }
                              />
                              {r.admin_comment &&
                                !statusEdits[r.request_id]?.comment && (
                                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                    Current comment:{" "}
                                    <span className="italic">
                                      {r.admin_comment}
                                    </span>
                                  </p>
                                )}
                            </div>

                            <div className="flex justify-end">
                              <button
                                type="button"
                                onClick={() =>
                                  handleStatusUpdate(r.request_id)
                                }
                                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 dark:bg-indigo-500 dark:hover:bg-indigo-400"
                              >
                                <CheckCircle2 className="h-4 w-4" />
                                Update
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* If you later want to show simulated options, user choice, etc., you can add more cards here */}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 rounded-lg bg-slate-900 px-4 py-3 text-sm text-white shadow-lg dark:bg-slate-200 dark:text-slate-900">
          <div className="flex items-center gap-2">
            {toast.type === "error" ? (
              <AlertTriangle className="h-4 w-4 text-amber-400" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            )}
            <span>{toast.message}</span>
            <button
              className="ml-2 text-xs underline"
              onClick={() => setToast(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Resolve modal */}
      {resolveModal.open && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
              Mark request as resolved
            </h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              <span className="font-semibold">Request:</span>{" "}
              {resolveModal.requestText}
            </p>
            <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-200">
              Resolution notes (optional)
            </label>
            <textarea
              rows={4}
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              placeholder="Describe how this was resolved…"
              value={resolveModal.notes}
              onChange={(e) =>
                setResolveModal((prev) => ({ ...prev, notes: e.target.value }))
              }
            />

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() =>
                  setResolveModal({
                    open: false,
                    requestId: null,
                    requestText: "",
                    notes: "",
                  })
                }
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleResolve}
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400"
              >
                <CheckCircle2 className="h-4 w-4" />
                Confirm resolve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
