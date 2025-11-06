import { useEffect, useMemo, useState } from "react";
import { getAllRequests } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import StatusBadge from "../components/StatusBadge";
import { Shield, Search, Filter, RefreshCw, Eye, EyeOff, Key, ChevronDown, ChevronRight, DollarSign, Clock, Heart } from "lucide-react";

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
      });
  }, [items, category, urgency, status, search]);

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="rounded-full bg-gradient-to-r from-slate-600 to-gray-700 p-3">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="mt-1 text-gray-600">View and manage all system requests</p>
            </div>
          </div>

          <div className="rounded-xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex items-center gap-2">
              <Key className="h-5 w-5 text-gray-500" />
              <label className="text-sm font-semibold text-gray-700">Admin API Key</label>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <input
                  type={showKey ? "text" : "password"}
                  placeholder="Enter admin API key"
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-2 pr-10 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <button
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              <button
                onClick={saveKey}
                className="rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-2 font-semibold text-white shadow-md transition-all hover:shadow-lg"
              >
                Save
              </button>
              <button
                onClick={clearKey}
                className="rounded-lg border-2 border-gray-300 px-6 py-2 font-semibold text-gray-700 transition-all hover:bg-gray-50"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        <div className="mb-6 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-1 items-center gap-2 rounded-lg bg-white px-4 py-2 shadow-md">
              <Search className="h-4 w-4 text-gray-500" />
              <input
                placeholder="Search by ID, resident, or message..."
                className="flex-1 border-0 bg-transparent text-sm focus:outline-none"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
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

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg bg-white px-4 py-2 shadow-md">
              <Filter className="h-4 w-4 text-gray-500" />
              <select
                className="border-0 bg-transparent text-sm focus:outline-none"
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
              className="rounded-lg bg-white px-4 py-2 text-sm shadow-md focus:outline-none"
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
              className="rounded-lg bg-white px-4 py-2 text-sm shadow-md focus:outline-none"
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
              className="rounded-lg bg-white px-4 py-2 text-sm shadow-md focus:outline-none"
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
              className="rounded-lg bg-white px-4 py-2 text-sm font-semibold shadow-md transition-all hover:bg-gray-50"
            >
              {sortDir === "asc" ? "↑ Asc" : "↓ Desc"}
            </button>
            <div className="ml-auto rounded-lg bg-white px-4 py-2 shadow-md">
              <span className="text-sm font-semibold text-gray-700">
                {sorted.length} {sorted.length === 1 ? "request" : "requests"}
              </span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center rounded-2xl bg-white p-12 shadow-xl">
            <LoadingSpinner label="Loading all requests..." />
          </div>
        ) : error ? (
          <div className="rounded-2xl bg-red-50 border-2 border-red-200 p-6 shadow-xl">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        ) : sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl bg-white p-12 shadow-xl">
            <p className="text-lg font-semibold text-gray-600">No data available</p>
            <p className="mt-2 text-sm text-gray-500">
              {apiKey ? "No requests match your filters" : "Enter API key to view requests"}
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
                <tbody className="divide-y divide-gray-200 bg-white">
                  {sorted.map((r) => (
                    <>
                      <tr key={r.request_id} className="transition-colors hover:bg-blue-50">
                        <td className="whitespace-nowrap px-6 py-4">
                          <code className="rounded bg-gray-100 px-2 py-1 text-xs font-mono text-gray-800">
                            {r.request_id}
                          </code>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                          {r.resident_id}
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
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                          {r.classification_confidence != null ? (
                            <span className="font-semibold">{Math.round(r.classification_confidence * 100)}%</span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                          {r.risk_forecast != null ? (
                            <span className={`font-semibold ${r.risk_forecast > 0.7 ? 'text-red-600' : r.risk_forecast > 0.3 ? 'text-yellow-600' : 'text-green-600'}`}>
                              {Math.round(r.risk_forecast * 100)}%
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                          {r.simulated_options?.length > 0 ? (
                            <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
                              {r.simulated_options.length} options
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                          {new Date(r.created_at).toLocaleString()}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <button
                            onClick={() => setExpandedRow(expandedRow === r.request_id ? null : r.request_id)}
                            className="text-blue-600 hover:text-blue-800 transition-colors"
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
                          <td colSpan="10" className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-6">
                            <div className="space-y-4">
                              {/* Message */}
                              <div className="rounded-lg bg-white p-4 shadow">
                                <h4 className="mb-2 text-sm font-semibold text-gray-700">Original Message</h4>
                                <p className="text-sm text-gray-900">{r.message_text}</p>
                              </div>

                              {/* Simulation Options */}
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
                                              ${opt.estimated_cost.toFixed(2)}
                                            </span>
                                          </div>
                                          <div className="flex items-center justify-between text-xs">
                                            <span className="flex items-center gap-1 text-gray-600">
                                              <Clock className="h-3 w-3" />
                                              Time
                                            </span>
                                            <span className="font-semibold text-blue-600">
                                              {opt.time_to_resolution.toFixed(1)}h
                                            </span>
                                          </div>
                                          <div className="flex items-center justify-between text-xs">
                                            <span className="flex items-center gap-1 text-gray-600">
                                              <Heart className="h-3 w-3" />
                                              Satisfaction
                                            </span>
                                            <span className="font-semibold text-red-600">
                                              {(opt.resident_satisfaction_impact * 100).toFixed(0)}%
                                            </span>
                                          </div>
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
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
