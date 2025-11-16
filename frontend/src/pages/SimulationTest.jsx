import { useState } from "react";
import { Zap, DollarSign, Clock, Heart, AlertCircle, CheckCircle2 } from "lucide-react";
import LoadingSpinner from "../components/LoadingSpinner";

export default function SimulationTest() {
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState("Maintenance");
  const [urgency, setUrgency] = useState("High");
  const [riskScore, setRiskScore] = useState(0.85);
  const [simulationResult, setSimulationResult] = useState(null);
  const [error, setError] = useState("");

  const runSimulation = async () => {
    setLoading(true);
    setError("");
    setSimulationResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/v1/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          category: category,
          urgency: urgency,
          intent: "solve_problem",
          confidence: 0.95,
          risk_score: parseFloat(riskScore),
          issue_id: `TEST_${Date.now()}`,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSimulationResult(data);
    } catch (err) {
      setError(`Failed to run simulation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 0.7) return "text-red-600";
    if (score >= 0.4) return "text-yellow-600";
    return "text-green-600";
  };

  const getOptionColor = (index) => {
    const colors = [
      "from-blue-500 to-purple-500",
      "from-green-500 to-teal-500",
      "from-orange-500 to-red-500",
    ];
    return colors[index] || colors[0];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-white shadow-lg">
            <Zap className="h-5 w-5" />
            <h1 className="text-2xl font-bold">Simulation Agent Test</h1>
          </div>
          <p className="mt-3 text-gray-600">
            Generate resolution options with SimPy simulation
          </p>
        </div>

        {/* Input Controls */}
        <div className="mb-6 rounded-2xl bg-white p-6 shadow-xl">
          <h2 className="mb-4 text-lg font-bold text-gray-900">Simulation Parameters</h2>

          <div className="grid gap-4 md:grid-cols-3">
            {/* Category */}
            <div>
              <label className="mb-2 block text-sm font-semibold text-gray-700">Category</label>
              <select
                className="w-full rounded-lg border-2 border-gray-200 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="Maintenance">Maintenance</option>
                <option value="Security">Security</option>
                <option value="Billing">Billing</option>
                <option value="Deliveries">Deliveries</option>
                <option value="Amenities">Amenities</option>
              </select>
            </div>

            {/* Urgency */}
            <div>
              <label className="mb-2 block text-sm font-semibold text-gray-700">Urgency</label>
              <select
                className="w-full rounded-lg border-2 border-gray-200 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                value={urgency}
                onChange={(e) => setUrgency(e.target.value)}
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>

            {/* Risk Score */}
            <div>
              <label className="mb-2 block text-sm font-semibold text-gray-700">
                Risk Score: <span className={`font-bold ${getRiskColor(riskScore)}`}>{riskScore}</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                className="w-full"
                value={riskScore}
                onChange={(e) => setRiskScore(parseFloat(e.target.value))}
              />
              <div className="mt-1 flex justify-between text-xs text-gray-500">
                <span>Low (0.0)</span>
                <span>Medium (0.5)</span>
                <span>High (1.0)</span>
              </div>
            </div>
          </div>

          {/* Run Button */}
          <div className="mt-6 flex items-center gap-4">
            <button
              onClick={runSimulation}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-3 font-semibold text-white shadow-lg transition-all hover:from-indigo-700 hover:to-purple-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <>
                  <LoadingSpinner label="" />
                  <span>Running Simulation...</span>
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5" />
                  <span>Run Simulation</span>
                </>
              )}
            </button>

            {error && (
              <div className="flex items-center gap-2 text-red-600">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm">{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* Results */}
        {simulationResult && (
          <div className="space-y-6">
            <div className="rounded-xl bg-gradient-to-r from-green-50 to-emerald-50 p-4 shadow-lg">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-semibold">Simulation Complete!</span>
                <code className="ml-auto rounded bg-green-100 px-3 py-1 text-xs font-mono">
                  {simulationResult.issue_id}
                </code>
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {simulationResult.options.map((option, idx) => (
                <div
                  key={option.option_id}
                  className="group rounded-2xl bg-white p-6 shadow-xl transition-all hover:scale-105 hover:shadow-2xl"
                >
                  {/* Option Header */}
                  <div
                    className={`mb-4 flex items-center gap-2 rounded-lg bg-gradient-to-r ${getOptionColor(
                      idx
                    )} p-3 text-white shadow-md`}
                  >
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/20 font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-sm font-bold">Option {idx + 1}</span>
                  </div>

                  {/* Action Description */}
                  <div className="mb-4">
                    <h3 className="text-lg font-bold text-gray-900">{option.action}</h3>
                  </div>

                  {/* Metrics */}
                  <div className="space-y-3">
                    {/* Cost */}
                    <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-green-600" />
                        <span className="text-sm font-semibold text-gray-700">Cost</span>
                      </div>
                      <span className="text-lg font-bold text-green-600">
                        ${option.estimated_cost.toFixed(2)}
                      </span>
                    </div>

                    {/* Time */}
                    <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-semibold text-gray-700">Time</span>
                      </div>
                      <span className="text-lg font-bold text-blue-600">
                        {option.time_to_resolution.toFixed(1)}h
                      </span>
                    </div>

                    {/* Satisfaction */}
                    <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                      <div className="flex items-center gap-2">
                        <Heart className="h-4 w-4 text-red-600" />
                        <span className="text-sm font-semibold text-gray-700">Satisfaction</span>
                      </div>
                      <span className="text-lg font-bold text-red-600">
                        {(option.resident_satisfaction_impact * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Option ID */}
                  <div className="mt-4 border-t border-gray-200 pt-3">
                    <code className="text-xs text-gray-500">{option.option_id}</code>
                  </div>
                </div>
              ))}
            </div>

            {/* Trade-off Analysis */}
            <div className="rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 p-6 shadow-xl">
              <h3 className="mb-4 text-lg font-bold text-gray-900">📊 Trade-off Analysis</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg bg-white p-4 shadow-md">
                  <div className="mb-2 text-sm font-semibold text-gray-600">Most Expensive</div>
                  <div className="text-2xl font-bold text-green-600">
                    ${Math.max(...simulationResult.options.map((o) => o.estimated_cost)).toFixed(2)}
                  </div>
                </div>
                <div className="rounded-lg bg-white p-4 shadow-md">
                  <div className="mb-2 text-sm font-semibold text-gray-600">Fastest</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.min(...simulationResult.options.map((o) => o.time_to_resolution)).toFixed(1)}h
                  </div>
                </div>
                <div className="rounded-lg bg-white p-4 shadow-md">
                  <div className="mb-2 text-sm font-semibold text-gray-600">Best Satisfaction</div>
                  <div className="text-2xl font-bold text-red-600">
                    {(
                      Math.max(...simulationResult.options.map((o) => o.resident_satisfaction_impact)) * 100
                    ).toFixed(0)}
                    %
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        {!simulationResult && !loading && (
          <div className="rounded-2xl bg-white p-8 text-center shadow-xl">
            <Zap className="mx-auto mb-4 h-12 w-12 text-indigo-500" />
            <h3 className="mb-2 text-lg font-bold text-gray-900">Ready to Test</h3>
            <p className="text-gray-600">
              Select a category, urgency level, and risk score, then click "Run Simulation" to see the
              resolution options generated by the SimPy-based simulation agent.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
