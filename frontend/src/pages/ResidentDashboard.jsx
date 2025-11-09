import { useEffect, useState } from "react";
import { useUser } from "../context/UserContext";
import { getResidentRequests, resolveRequest } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import { RefreshCw, Filter, Search, FileText, Calendar, User, CheckCircle2, X } from "lucide-react";

export default function ResidentDashboard() {
  const { residentId, setResidentId } = useUser();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [statusFilter, setStatusFilter] = useState("All");
  const [toast, setToast] = useState(null);
  const [resolveModal, setResolveModal] = useState(null); // {requestId, requestText}
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [resolving, setResolving] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await getResidentRequests(residentId);
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError("Failed to fetch requests. Check backend connection.");
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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Requests</h1>
              <p className="mt-2 text-gray-600">View and track all your submitted requests</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg bg-white px-4 py-2 shadow-md">
                <User className="h-4 w-4 text-gray-500" />
                <input
                  className="w-40 border-0 bg-transparent text-sm focus:outline-none"
                  placeholder="Resident ID"
                  value={residentId}
                  onChange={(e) => setResidentId(e.target.value)}
                />
              </div>
              <button
                onClick={load}
                className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:shadow-lg"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg bg-white px-4 py-2 shadow-md">
              <Filter className="h-4 w-4 text-gray-500" />
              <select
                className="border-0 bg-transparent text-sm focus:outline-none"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                {["All", "Submitted", "Processing", "In Progress", "Resolved", "Escalated"].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="rounded-lg bg-white px-4 py-2 shadow-md">
              <span className="text-sm font-semibold text-gray-700">
                {filtered.length} {filtered.length === 1 ? "request" : "requests"}
              </span>
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
