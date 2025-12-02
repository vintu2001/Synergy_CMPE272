import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { submitRequest } from "../services/api";
import { useUser } from "../context/UserContext";
import LoadingSpinner from "../components/LoadingSpinner";
import Toast from "../components/Toast";
import PreferencesForm from "../components/PreferencesForm";
import { Send, AlertCircle, CheckCircle2, User, UserX, Info, Layers } from "lucide-react";

export default function ResidentSubmission() {
  const { residentId, residentName, setResidentId, setResidentName } = useUser();
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
  const [submitting, setSubmitting] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [toast, setToast] = useState(null);
  const [error, setError] = useState("");
  const [submittedResult, setSubmittedResult] = useState(null);
  const [preferences, setPreferences] = useState(null);

  const charCount = useMemo(() => messageText.length || 0, [messageText]);

  useEffect(() => {
    if (!residentId) {
      setValue("message_text", "");
    }
  }, [residentId, setValue]);

  const handleSubmit = async () => {
    if (!residentId) {
      setToast({ message: "Please enter your apartment number before submitting.", type: "error" });
      return;
    }

    if (!messageText || messageText.trim().length < 10) {
      setToast({ message: "Please describe your issue with at least 10 characters.", type: "error" });
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const category = watch("category") || analysis?.category;
      const urgency = watch("urgency") || analysis?.urgency;
      const result = await submitRequest(residentId, messageText, category, urgency, preferences);

      // Check if this was a question that got answered
      if (result.status === "answered") {
        setToast({
          message: "Your question has been answered!",
          type: "success",
        });

        // Show the answer in a nice format
        setSubmittedResult({
          ...result,
          isQuestion: true
        });

        // Don't auto-reset - let user read and manually clear if they want
        return;
      }

      // Check if LLM generation failed
      if (result.status === "error") {
        setError(result.message);
        setToast({
          message: result.message,
          type: "error"
        });

        // Store error result with request_id so user can escalate
        setSubmittedResult({
          ...result,
          isError: true,
          escalation_required: result.escalation_required || false
        });
        return;
      }

      // Success! Show confirmation toast and clear form
      setToast({
        message: result.message || "Request submitted successfully! We're working on it.",
        type: "success",
      });

      // Store result to show confirmation
      setSubmittedResult(result);

      // Clear form after 2 seconds
      setTimeout(() => {
        reset();
        setAnalysis(null);
        setSubmittedResult(null);
        setPreferences(null);
      }, 3000);

    } catch (e) {
      setToast({ message: e.response?.data?.detail || "Unable to submit request. Please try again.", type: "error" });
      setError(e.response?.data?.detail || "Failed to submit request.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <section className="w-full px-4 py-10 sm:px-6 lg:px-10">
        <div className="space-y-8">
          <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Submit a new service request</h1>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                  Describe your issue with all the details for quick and appropriate resolution.
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
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
                    <Layers className="h-3.5 w-3.5" />
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
          </header>

          <div className="grid gap-6">
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">
                  Describe the issue in detail
                </label>
                <textarea
                  rows={7}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 transition focus:border-slate-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:bg-slate-900 dark:focus:ring-slate-800"
                  placeholder="Tell us what’s going on. Include room, equipment, or time details for faster resolution."
                  {...register("message_text", { required: true, minLength: 10 })}
                />
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className={charCount >= 10 ? "font-medium text-emerald-600 dark:text-emerald-300" : ""}>
                    {charCount} / 5000 characters
                  </span>
                  {errors.message_text && (
                    <span className="inline-flex items-center gap-1 text-rose-500">
                      <AlertCircle className="h-3.5 w-3.5" />
                      Minimum 10 characters required
                    </span>
                  )}
                </div>

                {/* Preferences Form */}
                <div className="mt-6">
                  <PreferencesForm preferences={preferences} onChange={setPreferences} />
                </div>

                <div className="mt-6 space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={handleSubmit}
                      disabled={submitting}
                      className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-300 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 dark:focus:ring-slate-700"
                    >
                      {submitting ? (
                        <>
                          <LoadingSpinner label="" />
                          <span>Submitting...</span>
                        </>
                      ) : (
                        <>
                          <Send className="h-4 w-4" />
                          <span>Submit request</span>
                        </>
                      )}
                    </button>
                    {error && <span className="text-sm text-rose-500">{error}</span>}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Display answer for questions */}
          {submittedResult && submittedResult.isQuestion && submittedResult.answer && (
            <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-6 shadow-lg dark:border-emerald-800 dark:from-emerald-950 dark:to-slate-900">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 rounded-full bg-emerald-100 p-2 dark:bg-emerald-900/40">
                  <CheckCircle2 className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div className="flex-1 space-y-3">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Here's your answer
                  </h3>
                  <div className="rounded-lg border border-emerald-200 bg-white p-4 dark:border-emerald-800 dark:bg-slate-950">
                    <p className="text-slate-700 dark:text-slate-200 leading-relaxed">
                      {submittedResult.answer.text}
                    </p>
                  </div>

                  {/* Sources */}
                  {((submittedResult.answer.source_docs || submittedResult.answer.sources)?.length > 0) && (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/50 mt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Info className="h-4 w-4 text-blue-500" />
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                          Sources consulted:
                        </p>
                      </div>
                      <div className="space-y-2">
                        {(submittedResult.answer.source_docs || submittedResult.answer.sources || []).map((source, idx) => (
                          <div key={idx} className="rounded border border-slate-200 bg-white p-2 dark:border-slate-700 dark:bg-slate-950">
                            <p className="text-[10px] font-mono text-blue-600 dark:text-blue-400 mb-1">
                              {source.doc_id || `Source ${idx + 1}`}
                            </p>
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              {source.text || source}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Confidence indicator */}
                  <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span>Confidence:</span>
                    <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                      <div
                        className="h-full rounded-full bg-emerald-500 transition-[width]"
                        style={{ width: `${Math.round((submittedResult.answer.confidence || 0) * 100)}%` }}
                      />
                    </div>
                    <span className="font-semibold text-slate-700 dark:text-slate-200">
                      {Math.round((submittedResult.answer.confidence || 0) * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
