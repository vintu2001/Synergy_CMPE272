import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { classifyMessage, submitRequest } from "../services/api";
import { useUser } from "../context/UserContext";
import LoadingSpinner from "../components/LoadingSpinner";
import Toast from "../components/Toast";
import { Sparkles, Send, AlertCircle, CheckCircle2, Clock, Zap } from "lucide-react";

const categoryColors = {
  Maintenance: "bg-blue-100 text-blue-800 border-blue-200",
  Billing: "bg-purple-100 text-purple-800 border-purple-200",
  Security: "bg-red-100 text-red-800 border-red-200",
  Deliveries: "bg-yellow-100 text-yellow-800 border-yellow-200",
  Amenities: "bg-green-100 text-green-800 border-green-200",
};

const urgencyColors = {
  High: "bg-red-100 text-red-800 border-red-300",
  Medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
  Low: "bg-blue-100 text-blue-800 border-blue-300",
};

export default function ResidentSubmission() {
  const { residentId, setResidentId } = useUser();
  const {
    register,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: { message_text: "", category: "", urgency: "", intent: "" },
  });

  const messageText = watch("message_text");
  const [analyzing, setAnalyzing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);
  const debounceRef = useRef(null);

  const charCount = useMemo(() => messageText.length || 0, [messageText]);

  useEffect(() => {
    if (!messageText || messageText.trim().length < 10) {
      setAnalysis(null);
      setError("");
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        setAnalyzing(true);
        setError("");
        const res = await classifyMessage(residentId, messageText);
        setAnalysis(res);
        // Always update from analysis to show AI suggestions
        setValue("category", res.category);
        setValue("urgency", res.urgency);
        setValue("intent", res.intent);
      } catch (e) {
        setError("Failed to analyze message. Check backend connection.");
      } finally {
        setAnalyzing(false);
      }
    }, 500);
    return () => clearTimeout(debounceRef.current);
  }, [messageText, residentId, setValue]);

  const handleSubmit = async () => {
    if (!messageText || messageText.trim().length < 10) {
      setToast({ message: "Please enter at least 10 characters", type: "error" });
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      // Get the current form values (user may have overridden AI suggestions)
      const category = watch("category") || analysis?.category;
      const urgency = watch("urgency") || analysis?.urgency;
      
      const result = await submitRequest(residentId, messageText, category, urgency);
      setToast({
        message: `Request submitted successfully! ID: ${result.request_id}`,
        type: "success",
      });
      reset();
      setAnalysis(null);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to submit request");
      setToast({ message: "Failed to submit request. Please try again.", type: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 text-white shadow-lg">
            <Sparkles className="h-5 w-5" />
            <h1 className="text-2xl font-bold">Submit a Request</h1>
          </div>
          <p className="mt-3 text-gray-600">Describe your issue and let AI help categorize it automatically</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="rounded-2xl bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <label className="text-sm font-semibold text-gray-700">Resident ID</label>
                <input
                  className="w-48 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="RES_1001"
                  value={residentId}
                  onChange={(e) => setResidentId(e.target.value)}
                />
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-semibold text-gray-700">Message</label>
                <textarea
                  rows={8}
                  className="w-full rounded-xl border-2 border-gray-200 bg-gray-50 px-4 py-3 text-gray-900 transition-all focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-100"
                  placeholder="Describe your issue in detail... (e.g., 'My air conditioning unit stopped working and it's getting very hot in my apartment')"
                  {...register("message_text", { required: true, minLength: 10 })}
                />
                <div className="flex items-center justify-between text-xs">
                  <span className={`${charCount >= 10 ? "text-green-600" : "text-gray-500"}`}>
                    {charCount} characters
                  </span>
                  {errors.message_text && (
                    <span className="flex items-center gap-1 text-red-600">
                      <AlertCircle className="h-3 w-3" />
                      Minimum 10 characters required
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-6 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting || !messageText || messageText.trim().length < 10}
                  className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 font-semibold text-white shadow-lg transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <LoadingSpinner label="" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-5 w-5" />
                      <span>Submit Request</span>
                    </>
                  )}
                </button>
                {analyzing && <LoadingSpinner label="Analyzing..." />}
                {error && <span className="text-sm text-red-600">{error}</span>}
              </div>
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="rounded-2xl bg-gradient-to-br from-purple-50 to-blue-50 p-6 shadow-xl">
              <div className="mb-4 flex items-center gap-2">
                <Zap className="h-5 w-5 text-purple-600" />
                <h3 className="text-lg font-bold text-gray-900">AI Suggestions</h3>
              </div>

              {analysis ? (
                <div className="space-y-4">
                  <div className="rounded-xl bg-white p-4 shadow-md">
                    <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Category
                    </label>
                    <select
                      className={`w-full rounded-lg border-2 px-4 py-2 font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-200 ${
                        categoryColors[watch("category") || analysis.category] || categoryColors.Maintenance
                      }`}
                      {...register("category")}
                      value={watch("category") || analysis.category}
                      onChange={(e) => setValue("category", e.target.value)}
                    >
                      {["Maintenance", "Billing", "Security", "Deliveries", "Amenities"].map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">You can override the AI suggestion</p>
                  </div>

                  <div className="rounded-xl bg-white p-4 shadow-md">
                    <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Urgency
                    </label>
                    <select
                      className={`w-full rounded-lg border-2 px-4 py-2 font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-blue-200 ${
                        urgencyColors[watch("urgency") || analysis.urgency] || urgencyColors.Medium
                      }`}
                      {...register("urgency")}
                      value={watch("urgency") || analysis.urgency}
                      onChange={(e) => setValue("urgency", e.target.value)}
                    >
                      {["High", "Medium", "Low"].map((u) => (
                        <option key={u} value={u}>
                          {u}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">You can override the AI suggestion</p>
                  </div>

                  <div className="rounded-xl bg-white p-4 shadow-md">
                    <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Intent
                    </label>
                    <div className="rounded-lg border-2 border-gray-200 bg-gray-50 px-4 py-2">
                      <span className="font-semibold text-gray-800">
                        {analysis.intent === "solve_problem" ? "Solve Problem" : "Human Escalation"}
                      </span>
                    </div>
                  </div>

                  <div className="rounded-xl bg-white p-4 shadow-md">
                    <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Confidence
                    </label>
                    <div className="mt-2">
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="font-semibold text-gray-700">{Math.round(analysis.confidence * 100)}%</span>
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all"
                          style={{ width: `${analysis.confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center rounded-xl bg-white p-8 text-center">
                  <Clock className="mb-3 h-12 w-12 text-gray-400" />
                  <p className="text-sm font-medium text-gray-600">Type at least 10 characters</p>
                  <p className="mt-1 text-xs text-gray-500">AI will analyze your message automatically</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
