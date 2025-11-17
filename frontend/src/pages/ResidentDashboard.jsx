import { useEffect, useMemo, useState } from "react";
import { useUser } from "../context/UserContext";
import { getResidentRequests, resolveRequest } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import {
  Calendar,
  CheckCircle2,
  FileText,
  Filter,
  RefreshCw,
  User,
  UserCheck,
  X,
  Search,
} from "lucide-react";

export default function ResidentDashboard() {
  const { residentId, residentName, setResidentId, setResidentName } = useUser();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [statusFilter, setStatusFilter] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [toast, setToast] = useState(null);

  // Modal state for "Mark resolved"
  const [resolveModal, setResolveModal] = useState(null); // { requestId, requestText }
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
      setError(
        "We couldn't fetch your requests. Please check your connection and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [residentId]);

  const filtered = useMemo(() => {
    let list = [...items];

    if (statusFilter !== "All") {
      list = list.filter((item) => item.status === statusFilter);
    }

    if (searchTerm.trim()) {
      const q = searchTerm.trim().toLowerCase();
      list = list.filter(
        (item) =>
          item.request_id?.toLowerCase().includes(q) ||
          item.message_text?.toLowerCase().includes(q) ||
          item.category?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [items, statusFilter, searchTerm]);

  const handleResolve = async () => {
    if (!resolveModal) return;

    setResolving(true);
    try {
      await resolveRequest(
        resolveModal.requestId,
        "resident",
        resolutionNotes || null
      );
      setToast({
        message: "Request marked as resolved!",
        type: "success",
      });
      setResolveModal(null);
      setResolutionNotes("");
      load();
    } catch (e) {
      setToast({
        message: "Failed to resolve request. Please try again.",
        type: "error",
      });
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="w-full bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 min-h-screen">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50">
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        </div>
      )}

      <section className="w-full px-4 py-10 sm:px-6 lg:px-10">
        <div className="space-y-8">
          {/* Header + resident identity */}
          <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
                  Resident dashboard
                </h1>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                  View your requests, track their status, and mark issues as
                  resolved once they’re fixed. Any admin comments will appear
                  alongside your requests.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                  <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <User className="h-3.5 w-3.5" />
                    Resident name
                  </span>
                  <input
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                    placeholder="Your name"
                    value={residentName}
                    onChange={(e) => setResidentName(e.target.value)}
                  />
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                  <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <UserCheck className="h-3.5 w-3.5" />
                    Apartment / resident ID
                  </span>
                  <input
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                    placeholder="e.g., A-304"
                    value={residentId}
                    onChange={(e) => setResidentId(e.target.value)}
                  />
                </label>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                <FileText className="h-4 w-4" />
                Total requests ·{" "}
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  {items.length}
                </span>
              </div>
            </div>
          </header>

          {/* Filters row */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                className="border-0 bg-transparent focus:outline-none dark:bg-slate-900"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="All">All statuses</option>
                <option value="Submitted">Submitted</option>
                <option value="Processing">Processing</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Escalated">Escalated</option>
              </select>
            </div>

            <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                className="border-0 bg-transparent text-sm focus:outline-none dark:bg-slate-900"
                placeholder="Search by ID, message, or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <button
              onClick={load}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-60 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-slate-100"
            >
              <RefreshCw
                className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </button>
          </div>

          {/* Content */}
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <LoadingSpinner />
              </div>
            ) : error ? (
              <div className="px-6 py-10 text-center text-sm text-slate-600 dark:text-slate-300">
                {error}
              </div>
            ) : filtered.length === 0 ? (
              <div className="px-6 py-16 text-center text-sm text-slate-500 dark:text-slate-300">
                You don’t have any requests yet. Submit one from the{" "}
                <span className="font-medium">Request</span> page.
              </div>
            ) : (
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
                      <th className="px-6 py-3 text-left">Admin Comment</th>
                      <th className="px-6 py-3 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {filtered.map((item) => (
                      <tr
                        key={item.request_id}
                        className="hover:bg-slate-50 dark:hover:bg-slate-800/60"
                      >
                        <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                          {item.request_id}
                        </td>

                        <td className="max-w-xs px-6 py-4 text-slate-700 dark:text-slate-200">
                          <p className="truncate" title={item.message_text}>
                            {item.message_text}
                          </p>
                        </td>

                        <td className="whitespace-nowrap px-6 py-4">
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                            {item.category}
                          </span>
                        </td>

                        <td className="whitespace-nowrap px-6 py-4">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${
                              item.urgency === "High"
                                ? "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200"
                                : item.urgency === "Medium"
                                ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200"
                                : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200"
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
                            {item.created_at
                              ? new Date(
                                  item.created_at
                                ).toLocaleDateString()
                              : "-"}
                          </div>
                        </td>

                        {/* NEW: Admin comment visible to resident */}
                        <td className="max-w-xs px-6 py-4 text-slate-600 dark:text-slate-300">
                          {item.admin_comment ? (
                            <p
                              className="truncate text-xs sm:text-sm"
                              title={item.admin_comment}
                            >
                              {item.admin_comment}
                            </p>
                          ) : (
                            <span className="text-xs italic text-slate-400 dark:text-slate-500">
                              No comment yet
                            </span>
                          )}
                        </td>

                        <td className="whitespace-nowrap px-6 py-4">
                          {(item.status === "In Progress" ||
                            item.status === "IN_PROGRESS") && (
                            <button
                              onClick={() =>
                                setResolveModal({
                                  requestId: item.request_id,
                                  requestText: item.message_text,
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
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Resolve modal */}
      {resolveModal && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100">
                Mark as resolved
              </h3>
              <button
                onClick={() => {
                  setResolveModal(null);
                  setResolutionNotes("");
                }}
                className="rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mb-4">
              <p className="mb-2 text-sm text-gray-600 dark:text-slate-300">
                You’re about to mark this request as resolved:
              </p>
              <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-800 dark:bg-slate-800 dark:text-slate-100">
                {resolveModal.requestText}
              </div>
            </div>

            <div className="mb-4">
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-slate-200">
                Resolution notes (optional)
              </label>
              <textarea
                rows={4}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-indigo-400 dark:focus:ring-indigo-900"
                placeholder="Add a short note about how this was resolved..."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setResolveModal(null);
                  setResolutionNotes("");
                }}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                disabled={resolving}
                className="flex-1 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:from-emerald-600 hover:to-green-600 disabled:opacity-50"
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
