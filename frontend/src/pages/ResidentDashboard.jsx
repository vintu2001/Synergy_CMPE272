import { useEffect, useMemo, useState } from "react";
import { useUser } from "../context/UserContext";
import { getResidentRequests, resolveRequest } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import { Calendar, CheckCircle2, FileText, Filter, RefreshCw, User, UserCheck, X } from "lucide-react";
import { RefreshCw, Filter, Search, FileText, Calendar, User, CheckCircle2, X } from "lucide-react";

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
              Showing <span className="font-semibold text-slate-700 dark:text-slate-100">{filteredItems.length}</span>
              {filteredItems.length === 1 ? "request" : "requests"}
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
          ) : filteredItems.length === 0 ? (
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
                    {filteredItems.map((item) => (
                      <tr key={item.request_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/60">
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
                          {(item.status === "In Progress" || item.status === "IN_PROGRESS") && (
                            <button
                              onClick={() => setResolveModal({ requestId: item.request_id, requestText: item.message_text })}
                              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-200 dark:bg-emerald-400 dark:text-emerald-950 dark:hover:bg-emerald-300"
                            >
                              <CheckCircle2 className="h-4 w-4" />
                              Mark resolved
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </section>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {resolveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 py-8 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Confirm resolution</h3>
              <button
                onClick={() => {
                  setResolveModal(null);
                  setResolutionNotes("");
                }}
                className="rounded-full p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mb-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">
              {resolveModal.requestText}
            </div>

            <label className="mb-3 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              Resolution notes (optional)
            </label>
            <textarea
              rows={4}
              className="mb-4 w-full rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
              placeholder="How did you fix the issue?"
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
            />

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setResolveModal(null);
                  setResolutionNotes("");
                }}
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                disabled={resolving}
                className="flex-1 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-200 disabled:opacity-60 dark:bg-emerald-400 dark:text-emerald-950 dark:hover:bg-emerald-300"
              >
                {resolving ? "Processing..." : "Mark resolved"}
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center rounded-2xl bg-white p-12 shadow-xl">
            <LoadingSpinner label="Loading requests..." />
          </div>
        ) : error ? (
          <div className="rounded-2xl bg-red-50 border-2 border-red-200 p-6 shadow-xl">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl bg-white p-12 shadow-xl">
            <FileText className="mb-4 h-16 w-16 text-gray-400" />
            <p className="text-lg font-semibold text-gray-600">No requests found</p>
            <p className="mt-2 text-sm text-gray-500">
              {statusFilter === "All" ? "Submit your first request to get started!" : `No requests with status "${statusFilter}"`}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl bg-white shadow-xl">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Request ID
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Message
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Category
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Urgency
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Created
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {filtered.map((r) => (
                    <tr key={r.request_id} className="transition-colors hover:bg-blue-50">
                      <td className="whitespace-nowrap px-6 py-4">
                        <code className="rounded bg-gray-100 px-2 py-1 text-xs font-mono text-gray-800">
                          {r.request_id}
                        </code>
                      </td>
                      <td className="px-6 py-4">
                        <p className="max-w-md truncate text-sm text-gray-900" title={r.message_text}>
                          {r.message_text}
                        </p>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-800">
                          {r.category}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            r.urgency === "High"
                              ? "bg-red-100 text-red-800"
                              : r.urgency === "Medium"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {r.urgency}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Calendar className="h-4 w-4" />
                          {new Date(r.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {(r.status === "In Progress" || r.status === "IN_PROGRESS") && (
                          <button
                            onClick={() => setResolveModal({ requestId: r.request_id, requestText: r.message_text })}
                            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow-md transition-all hover:from-green-600 hover:to-emerald-600 hover:shadow-lg"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                            Mark as Resolved
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      
      {/* Toast Notifications */}
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
