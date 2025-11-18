import React, { useEffect, useMemo, useState } from "react";
import { getAllRequests, resolveRequest } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import StatusBadge from "../components/StatusBadge";
import { Shield, Search, Filter, RefreshCw, Eye, EyeOff, Key, ChevronDown, ChevronRight, DollarSign, Clock, Heart, AlertTriangle, UserX, CheckCircle2 } from "lucide-react";

export default function AdminDashboard() {
  const [apiKey, setApiKey] = useState(localStorage.getItem("admin_api_key") || "");
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [urgency, setUrgency] = useState("All");
  const [status, setStatus] = useState("All");
  const [sortField, setSortField] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");
  const [expandedRow, setExpandedRow] = useState(null);
  const [urgentOnly, setUrgentOnly] = useState(false);
  const [requireHumanOnly, setRequireHumanOnly] = useState(false);
  const [escalatedOnly, setEscalatedOnly] = useState(false);
  const [resolveModal, setResolveModal] = useState(null);
  const [resolving, setResolving] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [toast, setToast] = useState(null);

  async function load() {
    if (!apiKey) return;
    setLoading(true);
    setError("");
    try {
      const res = await getAllRequests(apiKey);
      setItems(Array.isArray(res?.requests) ? res.requests : []);
    } catch (e) {
      setError("Failed to fetch admin data. Check API key.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (apiKey) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey]);

  const handleResolve = async () => {
    if (!resolveModal) return;
    
    setResolving(true);
    try {
      await resolveRequest(resolveModal.requestId, "admin", resolutionNotes || null);
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

  const filtered = useMemo(() => {
    return items
      .filter((r) => (category === "All" ? true : r.category === category))
      .filter((r) => (urgency === "All" ? true : r.urgency === urgency))
      .filter((r) => (status === "All" ? true : r.status === status))
      .filter((r) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (
          r.request_id?.toLowerCase().includes(q) ||
          r.resident_id?.toLowerCase().includes(q) ||
          r.message_text?.toLowerCase().includes(q)
        );
      })
      .filter((r) => (urgentOnly ? r.urgency === "High" : true))
      .filter((r) => {
        if (!requireHumanOnly) return true;
        return r.intent === "human_escalation" || r.user_selected_option_id === "escalate_to_human";
      })
      .filter((r) => {
        if (!escalatedOnly) return true;
        return r.status === "Escalated" || r.user_selected_option_id === "escalate_to_human";
      });
  }, [items, category, urgency, status, search, urgentOnly, requireHumanOnly, escalatedOnly]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      const av = a[sortField];
      const bv = b[sortField];
      if (sortField.includes("created") || sortField.includes("updated")) {
        const ad = new Date(av).getTime();
        const bd = new Date(bv).getTime();
        return sortDir === "asc" ? ad - bd : bd - ad;
      }
      const as = String(av ?? "");
      const bs = String(bv ?? "");
      return sortDir === "asc" ? as.localeCompare(bs) : bs.localeCompare(as);
    });
    return arr;
  }, [filtered, sortField, sortDir]);

  function saveKey() {
    localStorage.setItem("admin_api_key", apiKey);
    load();
  }

  function clearKey() {
    localStorage.removeItem("admin_api_key");
    setApiKey("");
    setItems([]);
  }

  return (
    <div className="w-full bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <section className="w-full px-4 py-10 sm:px-6 lg:px-10">
        <div className="space-y-8">
          <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-full bg-slate-900 p-3 text-white shadow-md dark:bg-slate-100 dark:text-slate-900">
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Admin console</h1>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                  Monitor resident requests, identify escalations, and resolve issues quickly.
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                <Key className="h-4 w-4 text-slate-500 dark:text-slate-300" />
                Admin password
              </div>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
                <div className="relative flex-1">
                  <input
                    type={showKey ? "text" : "password"}
                    placeholder="Enter your admin password"
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 pr-10 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-700"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                  >
                    {showKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={saveKey}
                    className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-300 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
                  >
                    Save
                  </button>
                  <button
                    onClick={clearKey}
                    className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800 dark:focus:ring-slate-700"
                  >
                    Clear
                  </button>
                  <button
                    onClick={load}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800 dark:focus:ring-slate-700"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Refresh
                  </button>
                </div>
              </div>
            </div>
          </header>

          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                <Search className="h-4 w-4 text-slate-400" />
                <input
                  placeholder="Search by request ID, resident, or message..."
                  className="flex-1 border-0 bg-transparent focus:outline-none dark:bg-transparent"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                Total: <span className="font-semibold text-slate-800 dark:text-slate-100">{sorted.length}</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                <Filter className="h-4 w-4 text-slate-400" />
                <select
                  className="border-0 bg-transparent focus:outline-none dark:bg-transparent"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {["All", "Maintenance", "Billing", "Security", "Deliveries", "Amenities"].map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <select
                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                value={urgency}
                onChange={(e) => setUrgency(e.target.value)}
              >
                {["All", "High", "Medium", "Low"].map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
              <select
                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {["All", "Submitted", "Processing", "In Progress", "Resolved", "Escalated"].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <select
                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                value={sortField}
                onChange={(e) => setSortField(e.target.value)}
              >
                {["created_at", "updated_at", "category", "urgency", "status"].map((f) => (
                  <option key={f} value={f}>
                    Sort by {f.replace("_", " ")}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-700"
              >
                {sortDir === "asc" ? "↑ Asc" : "↓ Desc"}
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setUrgentOnly((prev) => !prev)}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold transition ${
                  urgentOnly
                    ? "bg-rose-500 text-white shadow-sm dark:bg-rose-400 dark:text-rose-950"
                    : "border border-slate-200 bg-white text-rose-600 shadow-sm hover:bg-rose-50 dark:border-rose-900/60 dark:bg-slate-900 dark:text-rose-300 dark:hover:bg-rose-900/30"
                }`}
              >
                <AlertTriangle className="h-3 w-3" />
                Urgent
              </button>
              <button
                onClick={() => setRequireHumanOnly((prev) => !prev)}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold transition ${
                  requireHumanOnly
                    ? "bg-purple-600 text-white shadow-sm dark:bg-purple-400 dark:text-purple-950"
                    : "border border-slate-200 bg-white text-purple-600 shadow-sm hover:bg-purple-50 dark:border-purple-900/60 dark:bg-slate-900 dark:text-purple-300 dark:hover:bg-purple-900/30"
                }`}
              >
                <UserX className="h-3 w-3" />
                Needs Human
              </button>
              <button
                onClick={() => setEscalatedOnly((prev) => !prev)}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold transition ${
                  escalatedOnly
                    ? "bg-amber-500 text-white shadow-sm dark:bg-amber-400 dark:text-amber-950"
                    : "border border-slate-200 bg-white text-amber-600 shadow-sm hover:bg-amber-50 dark:border-amber-900/60 dark:bg-slate-900 dark:text-amber-300 dark:hover:bg-amber-900/30"
                }`}
              >
                Escalated
              </button>
            </div>

            {/* Recurring Issues Alert Banner */}
            {items.filter((r) => r.recurring_issue_non_escalated).length > 0 && (
              <div className="rounded-lg border-2 border-amber-400 bg-gradient-to-r from-amber-50 to-orange-50 p-4 shadow-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 flex-shrink-0 text-amber-600" />
                  <div className="flex-1">
                    <h4 className="text-sm font-bold text-amber-900">
                      Recurring Issues Requiring Attention
                    </h4>
                    <p className="mt-1 text-xs text-amber-800">
                      {items.filter((r) => r.recurring_issue_non_escalated).length} user(s) have recurring issues but chose not to escalate. 
                      Please review these requests and consider reaching out to discuss permanent solutions.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

        {loading ? (
          <div className="flex items-center justify-center rounded-2xl border border-slate-200 bg-white p-16 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <LoadingSpinner label="Loading admin data..." />
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm font-medium text-rose-700 shadow-sm dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200">
            {error}
          </div>
        ) : sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <p className="text-base font-semibold text-slate-700 dark:text-slate-200">No requests to show</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {apiKey ? "Adjust your filters or refresh to see more data." : "Enter your admin password to load requests."}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Request ID
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Resident
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
                      Confidence
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Risk
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Options
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Created
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {sorted.map((r) => (
                    <React.Fragment key={r.request_id}>
                      <tr className={`hover:bg-slate-50 dark:hover:bg-slate-800/60 ${r.recurring_issue_non_escalated ? 'bg-amber-50/50 dark:bg-amber-900/20 border-l-4 border-amber-400' : ''}`}>
                        <td className="whitespace-nowrap px-6 py-4 text-xs text-slate-600 dark:text-slate-300">
                          <div className="flex items-center gap-2">
                            <code className="rounded bg-slate-100 px-2 py-1 font-mono text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                              {r.request_id}
                            </code>
                            {r.recurring_issue_non_escalated && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-200">
                                <AlertTriangle className="h-3 w-3" />
                                Recurring
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-slate-700 dark:text-slate-200">
                          {r.resident_id}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                            {r.category}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              r.urgency === "High"
                                ? "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200"
                                : r.urgency === "Medium"
                                ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200"
                                : "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200"
                            }`}
                          >
                            {r.urgency}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <StatusBadge status={r.status} />
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-slate-600 dark:text-slate-300">
                          {r.classification_confidence != null ? (
                            <span className="font-semibold">{Math.round(r.classification_confidence * 100)}%</span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-slate-600 dark:text-slate-300">
                          {r.risk_forecast != null ? (
                            <span
                              className={`font-semibold ${
                                r.risk_forecast > 0.7
                                  ? "text-rose-600"
                                  : r.risk_forecast > 0.3
                                  ? "text-amber-600"
                                  : "text-emerald-600"
                              }`}
                            >
                              {Math.round(r.risk_forecast * 100)}%
                            </span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-slate-600 dark:text-slate-300">
                          {r.simulated_options?.length > 0 ? (
                            <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200">
                              {r.simulated_options.length} options
                            </span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-slate-600 dark:text-slate-300">
                          {new Date(r.created_at).toLocaleString()}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <button
                            onClick={() => setExpandedRow(expandedRow === r.request_id ? null : r.request_id)}
                            className="text-slate-500 transition hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                          >
                            {expandedRow === r.request_id ? (
                              <ChevronDown className="h-5 w-5" />
                            ) : (
                              <ChevronRight className="h-5 w-5" />
                            )}
                          </button>
                        </td>
                      </tr>
                      {expandedRow === r.request_id && (
                        <tr key={`${r.request_id}-details`}>
                          <td colSpan="11" className="bg-slate-50 px-6 py-6 dark:bg-slate-800/50">
                            <div className="grid gap-4 md:grid-cols-2">
                              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
                                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Resident message</h4>
                                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{r.message_text}</p>
                              </div>

                              {/* Recurring Issue Non-Escalated Alert */}
                              {r.recurring_issue_non_escalated && (
                                <div className="rounded-lg border-2 border-amber-400 bg-gradient-to-r from-amber-50 to-orange-50 p-4 shadow-lg">
                                  <div className="flex items-start gap-3">
                                    <AlertTriangle className="h-5 w-5 flex-shrink-0 text-amber-600" />
                                    <div className="flex-1">
                                      <h4 className="mb-2 text-sm font-bold text-amber-900">⚠️ Recurring Issue Alert</h4>
                                      <p className="mb-2 text-sm text-amber-800">
                                        This user has been facing this issue <strong>frequently</strong> and chose an option other than escalating to admin.
                                      </p>
                                      <p className="text-xs text-amber-700">
                                        <strong>Action Required:</strong> Please check with the user if they need any help or if there are any concerns. 
                                        Consider reaching out to discuss a permanent solution for this recurring issue.
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* User Selection Info */}
                              {r.user_selected_option_id && (
                                <div className="rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 p-4 shadow">
                                  <h4 className="mb-2 text-sm font-semibold text-gray-700">✅ User Selection</h4>
                                  <div className="flex items-center gap-3">
                                    <span className="text-sm text-gray-900">
                                      User selected: <strong>{r.user_selected_option_id}</strong>
                                    </span>
                                    {r.recommended_option_id && (
                                      <>
                                        <span className="text-gray-400">•</span>
                                        {r.user_selected_option_id === r.recommended_option_id ? (
                                          <span className="flex items-center gap-1 text-sm font-semibold text-green-600">
                                            <CheckCircle2 className="h-4 w-4" />
                                            Matches AI recommendation
                                          </span>
                                        ) : (
                                          <span className="flex items-center gap-1 text-sm font-semibold text-orange-600">
                                            ⚠️ AI recommended: {r.recommended_option_id}
                                          </span>
                                        )}
                                      </>
                                    )}
                                  </div>
                                </div>
                              )}

                              {r.user_selected_option_id && (
                                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-900/20">
                                  <h4 className="text-sm font-semibold text-emerald-700 dark:text-emerald-200">Resident choice</h4>
                                  <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-100">
                                    Selected option <strong>{r.user_selected_option_id}</strong>
                                  </p>
                                  {r.recommended_option_id && r.user_selected_option_id !== r.recommended_option_id && (
                                    <p className="text-xs text-amber-600 dark:text-amber-300">AI suggested {r.recommended_option_id}</p>
                                  )}
                                </div>
                              )}

                              {r.simulated_options && r.simulated_options.length > 0 && (
                                <div>
                                  <h4 className="mb-3 text-sm font-semibold text-gray-700">
                                    🎯 Simulated Resolution Options
                                  </h4>
                                  <div className="grid gap-4 md:grid-cols-3">
                                    {r.simulated_options.map((opt, idx) => (
                                      <div
                                        key={opt.option_id}
                                        className="rounded-lg bg-white p-4 shadow-md transition-all hover:shadow-lg"
                                      >
                                        <div className="mb-3 flex items-center gap-2">
                                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-xs font-bold text-white">
                                            {idx + 1}
                                          </span>
                                          <span className="text-xs font-semibold text-gray-500">
                                            {opt.option_id}
                                          </span>
                                        </div>
                                        <h5 className="mb-3 text-sm font-bold text-gray-900">{opt.action}</h5>
                                        <div className="space-y-2">
                                          <div className="flex items-center justify-between text-xs">
                                            <span className="flex items-center gap-1 text-gray-600">
                                              <DollarSign className="h-3 w-3" />
                                              Cost
                                            </span>
                                            <span className="font-semibold text-green-600">
                                              ${Number(opt.estimated_cost).toFixed(2)}
                                            </span>
                                          </div>
                                          <div className="flex items-center justify-between text-xs">
                                            <span className="flex items-center gap-1 text-gray-600">
                                              <Clock className="h-3 w-3" />
                                              Time
                                            </span>
                                            <span className="font-semibold text-blue-600">
                                              {Number(opt.estimated_time).toFixed(1)}h
                                            </span>
                                          </div>
                                          {opt.resident_satisfaction_impact != null && (
                                            <div className="flex items-center justify-between text-xs">
                                              <span className="flex items-center gap-1 text-gray-600">
                                                <Heart className="h-3 w-3" />
                                                Satisfaction
                                              </span>
                                              <span className="font-semibold text-red-600">
                                                {(Number(opt.resident_satisfaction_impact) * 100).toFixed(0)}%
                                              </span>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
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
    </div>
  );
}
