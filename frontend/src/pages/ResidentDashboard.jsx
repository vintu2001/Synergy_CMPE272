import React, { useEffect, useMemo, useState } from "react";
import { useUser } from "../context/UserContext";
import { getResidentRequests, resolveRequest } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import { Calendar, CheckCircle2, FileText, Filter, RefreshCw, User, UserCheck, X, Search, MessageSquare } from "lucide-react";

export default function ResidentDashboard() {
  const { residentId, residentName, setResidentId, setResidentName } = useUser();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [statusFilter, setStatusFilter] = useState("All");
  const [toast, setToast] = useState(null);
  const [resolveModal, setResolveModal] = useState(null); // {requestId, requestText}
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [resolving, setResolving] = useState(false);

  async function load() {
    if (!residentId) {
      setItems([]);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await getResidentRequests(residentId);
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError("We couldn't fetch your requests. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [residentId]);

  const handleResolve = async () => {
    if (!resolveModal) return;
    
    setResolving(true);
    try {
      await resolveRequest(resolveModal.requestId, "resident", resolutionNotes || null);
      setToast({ message: "Request marked as resolved!", type: "success" });
      setResolveModal(null);
      setResolutionNotes("");
      // Reload requests
      load();
    } catch (e) {
      setToast({ message: "Failed to resolve request. Please try again.", type: "error" });
    } finally {
      setResolving(false);
    }
  };

  const filtered = items.filter((i) => (statusFilter === "All" ? true : i.status === statusFilter));

  return (
    <div className="w-full bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <section className="w-full px-4 py-10 sm:px-6 lg:px-10">
        <div className="space-y-8">
          <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Resident dashboard</h1>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                  View every request you've made, track the status, and let us know when something is resolved.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                  <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <User className="h-3.5 w-3.5" />
                    Resident name
                  </span>
                  <input
                    className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                    placeholder="Your name"
                    value={residentName}
                    onChange={(e) => setResidentName(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                  <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <UserCheck className="h-3.5 w-3.5" />
                    Apartment number
                  </span>
                  <input
                    className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                    placeholder="e.g., RES_1001"
                    value={residentId}
                    onChange={(e) => setResidentId(e.target.value)}
                  />
                </label>
              </div>
            </div>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                onClick={load}
                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-300 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 dark:focus:ring-slate-700"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh requests
              </button>
              <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                Total requests · <span className="font-semibold text-slate-700 dark:text-slate-100">{items.length}</span>
              </div>
            </div>
          </header>

          <div className="flex flex-wrap items-center gap-3">
            <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                className="border-0 bg-transparent focus:outline-none dark:bg-slate-900"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                {["All", "Submitted", "Processing", "In Progress", "Resolved", "Escalated"].map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </div>

            <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              Showing <span className="font-semibold text-slate-700 dark:text-slate-100">{filtered.length}</span>
              {filtered.length === 1 ? "request" : "requests"}
              {statusFilter !== "All" && (
                <span className="rounded-full bg-slate-200 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {statusFilter}
                </span>
              )}
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center rounded-2xl border border-slate-200 bg-white p-16 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <LoadingSpinner label="Loading your requests..." />
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700 shadow-sm dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200">
              {error}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <FileText className="h-10 w-10 text-slate-400" />
              <p className="text-base font-semibold text-slate-700 dark:text-slate-200">No requests found</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {statusFilter === "All"
                  ? "Submit a new request to get started."
                  : `You have no requests marked as ${statusFilter}.`}
              </p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
                  <thead>
                    <tr className="bg-slate-100 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                      <th className="px-6 py-3 text-left">Request ID</th>
                      <th className="px-6 py-3 text-left">Message</th>
                      <th className="px-6 py-3 text-left">Category</th>
                      <th className="px-6 py-3 text-left">Urgency</th>
                      <th className="px-6 py-3 text-left">Status</th>
                      <th className="px-6 py-3 text-left">Created</th>
                      <th className="px-6 py-3 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {filtered.map((item) => (
                      <React.Fragment key={item.request_id}>
                        <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/60">
                          <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                            {item.request_id}
                          </td>
                          <td className="max-w-xs px-6 py-4 text-slate-700 dark:text-slate-200">
                            <p className="truncate" title={item.message_text}>
                              {item.message_text}
                            </p>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                              {item.category}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <span
                              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                                item.urgency === "High"
                                  ? "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200"
                                  : item.urgency === "Medium"
                                  ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200"
                                  : "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200"
                              }`}
                            >
                              {item.urgency}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <StatusBadge status={item.status} />
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-slate-600 dark:text-slate-300">
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4" />
                              {new Date(item.created_at).toLocaleDateString()}
                            </div>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <div className="flex items-center gap-2">
                              {(item.status === "In Progress" || item.status === "IN_PROGRESS") && (
                                <button
                                  onClick={() => setResolveModal({ requestId: item.request_id, requestText: item.message_text })}
                                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-200 dark:bg-emerald-400 dark:text-emerald-950 dark:hover:bg-emerald-300"
                                >
                                  <CheckCircle2 className="h-4 w-4" />
                                  Mark resolved
                                </button>
                              )}
                              {item.admin_comments && item.admin_comments.length > 0 && (
                                <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" title={`${item.admin_comments.length} admin comment(s)`}>
                                  <MessageSquare className="h-3 w-3" />
                                  {item.admin_comments.length}
                                </span>
                              )}
                            </div>
                          </td>
                        </tr>
                        {item.admin_comments && item.admin_comments.length > 0 && (
                          <tr className="bg-blue-50/50 dark:bg-blue-900/10">
                            <td colSpan="7" className="px-6 py-4">
                              <div className="rounded-lg border border-blue-200 bg-white p-4 dark:border-blue-800 dark:bg-slate-900">
                                <div className="mb-2 flex items-center gap-2">
                                  <MessageSquare className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                                  <h4 className="text-xs font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-300">
                                    Admin Comments
                                  </h4>
                                </div>
                                <div className="space-y-2">
                                  {item.admin_comments.map((comment, idx) => (
                                    <div key={idx} className="rounded-lg border border-blue-100 bg-blue-50/50 p-3 dark:border-blue-800/50 dark:bg-blue-900/20">
                                      <p className="text-sm text-slate-700 dark:text-slate-200">{comment.comment}</p>
                                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                        {new Date(comment.added_at).toLocaleString()}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </section>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      {/* Resolve Modal */}
      {resolveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-gray-900">Mark as Resolved</h3>
              <button
                onClick={() => {
                  setResolveModal(null);
                  setResolutionNotes("");
                }}
                className="rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <p className="mb-2 text-sm text-gray-600">Request:</p>
              <p className="rounded-lg bg-gray-50 p-3 text-sm text-gray-900">
                {resolveModal.requestText}
              </p>
            </div>
            
            <div className="mb-6">
              <label className="mb-2 block text-sm font-semibold text-gray-700">
                Resolution Notes (Optional)
              </label>
              <textarea
                rows={4}
                className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 text-sm transition-all focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                placeholder="Add any notes about how the issue was resolved..."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
              />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setResolveModal(null);
                  setResolutionNotes("");
                }}
                className="flex-1 rounded-lg border-2 border-gray-300 px-4 py-2 font-semibold text-gray-700 transition-all hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                disabled={resolving}
                className="flex-1 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 px-4 py-2 font-semibold text-white shadow-md transition-all hover:from-green-600 hover:to-emerald-600 disabled:opacity-50"
              >
                {resolving ? "Processing..." : "Confirm Resolution"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
