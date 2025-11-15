import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { classifyMessage, submitRequest, selectOption } from "../services/api";
import { useUser } from "../context/UserContext";
import LoadingSpinner from "../components/LoadingSpinner";
import Toast from "../components/Toast";
import { Sparkles, Send, AlertCircle, CheckCircle2, Clock, Zap, DollarSign, Heart, Star, User, UserX, ChevronDown, ChevronUp, Info, Layers, Settings2, ShieldCheck, SlidersHorizontal } from "lucide-react";

const categoryStyles = {
  Maintenance: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200",
  Billing: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-200",
  Security: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200",
  Deliveries: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
  Amenities: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200",
};

const urgencyStyles = {
  High: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200",
  Medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
  Low: "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200",
};

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
  const [analyzing, setAnalyzing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [toast, setToast] = useState(null);
  const [error, setError] = useState("");
  const [submittedResult, setSubmittedResult] = useState(null);
  const [selectingOption, setSelectingOption] = useState(false);
  const debounceRef = useRef(null);
  
  // NEW: State for option selection flow - allow multiple options to be expanded
  const [expandedOptions, setExpandedOptions] = useState(new Set()); // Track which options' details are expanded

  const charCount = useMemo(() => messageText.length || 0, [messageText]);
  
  // Toggle function for expanding/collapsing option details
  const toggleOptionDetails = (optionId) => {
    setExpandedOptions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(optionId)) {
        newSet.delete(optionId);
      } else {
        newSet.add(optionId);
      }
      return newSet;
    });
  };
  
  // Parse action text into steps for display
  const parseActionSteps = (action, reasoning) => {
    const steps = [];
    
    // Try to extract steps from action text
    const text = action + ' ' + reasoning;
    
    // Look for numbered steps or sequential actions
    const numberedSteps = text.match(/\d+[.)]\s*[^.]+\./g);
    if (numberedSteps && numberedSteps.length > 0) {
      return numberedSteps.map(s => s.replace(/^\d+[.)]\s*/, '').trim());
    }
    
    // Look for "first", "then", "finally" patterns
    const sequentialPattern = /(first|then|next|after|finally)[,:]?\s*([^.]+)/gi;
    let match;
    while ((match = sequentialPattern.exec(text)) !== null) {
      steps.push(match[2].trim());
    }
    if (steps.length > 0) return steps;
    
    // Look for action keywords
    const actionKeywords = ['contact', 'dispatch', 'schedule', 'send', 'perform', 'check', 'repair', 'replace', 'inspect'];
    const sentences = text.split(/[.;]/).filter(s => s.trim());
    
    for (const sentence of sentences) {
      const lowerSentence = sentence.toLowerCase();
      if (actionKeywords.some(keyword => lowerSentence.includes(keyword))) {
        const cleaned = sentence.trim();
        if (cleaned.length > 10) {
          steps.push(cleaned);
        }
      }
    }
    
    // If we still have no steps, create basic steps from the action
    if (steps.length === 0) {
      if (action.toLowerCase().includes('emergency') || action.toLowerCase().includes('immediate')) {
        steps.push('Emergency service dispatch initiated');
        steps.push('Technician assigned for immediate response');
        steps.push('Issue resolution and verification');
      } else if (action.toLowerCase().includes('schedule')) {
        steps.push('Service appointment scheduled');
        steps.push('Technician visits and diagnoses issue');
        steps.push('Repair completed and tested');
      } else {
        steps.push('Initial assessment of the issue');
        steps.push('Appropriate action taken');
        steps.push('Follow-up to ensure resolution');
      }
    }
    
    return steps.slice(0, 5); // Limit to 5 steps max
  };

  useEffect(() => {
    if (!residentId) {
      setValue("message_text", "");
    }
  }, [residentId, setValue]);

  useEffect(() => {
    if (!messageText || messageText.trim().length < 10 || !residentId) {
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
        setValue("category", res.category);
        setValue("urgency", res.urgency);
        setValue("intent", res.intent);
      } catch (e) {
        setError("We couldn't analyze the message. Check your connection and try again.");
      } finally {
        setAnalyzing(false);
      }
    }, 450);

    return () => clearTimeout(debounceRef.current);
  }, [messageText, residentId, setValue]);

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
      const result = await submitRequest(residentId, messageText, category, urgency);
      
      // Check if LLM generation failed
      if (result.status === "error") {
        setError(result.message);
        setToast({
          message: result.message,
          type: "error"
        });
        
        // Show escalation message in a modal or alert
        setTimeout(() => {
          alert(`⚠️ LLM Generation Failed\n\n${result.message}\n\n${result.action_required}\n\nPlease use the "Escalate to Human" option.`);
        }, 500);
        return;
      }
      
      // Store result and show option selection
      setSubmittedResult(result);
      setToast({
        message: `Request classified! Please select a resolution option.`,
        type: "success",
      });
    } catch (e) {
      setToast({ message: e.response?.data?.detail || "Unable to submit request. Please try again.", type: "error" });
      setError(e.response?.data?.detail || "Failed to submit request.");
    } finally {
      setSubmitting(false);
    }
  };
  
  // NEW: Handle option selection
  const handleSelectOption = async (optionId) => {
    if (!submittedResult) return;
    
    setSelectingOption(true);
    try {
      const result = await selectOption(submittedResult.request_id, optionId);
      setToast({
        message: `Option selected successfully! Your request is now being processed.`,
        type: "success",
      });
      
      // Reset form after option selection
      setTimeout(() => {
        reset();
        setAnalysis(null);
        setSubmittedResult(null);
      }, 2000);
    } catch (e) {
      setToast({ 
        message: "Failed to select option. Please try again.", 
        type: "error" 
      });
    } finally {
      setSelectingOption(false);
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
                  Provide a clear description of your issue. Our AI will suggest the best category and urgency, and you can choose how you want it resolved.
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

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
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
                <div className="mt-6 flex flex-wrap items-center gap-3">
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
                  {analyzing && <LoadingSpinner label="Analyzing..." />}
                  {error && <span className="text-sm text-rose-500">{error}</span>}
                </div>
              </div>
            </div>

            <aside className="space-y-6">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="mb-4 flex items-center gap-2">
                  <Settings2 className="h-4 w-4 text-slate-500" />
                  <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">AI classification</h3>
                </div>
                {analysis ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Suggested category</p>
                      <select
                        className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
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
                    </div>

                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Suggested urgency</p>
                      <select
                        className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
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
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">
                      <span>Intent</span>
                      <span>{analysis.intent === "solve_problem" ? "Solve problem" : "Human escalation"}</span>
                    </div>

                    <div className="space-y-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-950">
                      <p className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        <span>Confidence</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-200">
                          {Math.round((analysis.confidence || 0) * 100)}%
                        </span>
                      </p>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                        <div
                          className="h-full rounded-full bg-slate-900 transition-[width] dark:bg-slate-100"
                          style={{ width: `${Math.round((analysis.confidence || 0) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 p-6 text-center dark:border-slate-700">
                    <SlidersHorizontal className="mb-3 h-8 w-8 text-slate-400" />
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Start typing above</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">AI suggestions appear automatically once your message is long enough.</p>
                  </div>
                )}
              </div>

              {analysis && (
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Quick overview</p>
                  <div className="space-y-3 text-sm">
                    <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
                      categoryStyles[watch("category") || analysis.category] || "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    }`}>
                      Category · {watch("category") || analysis.category}
                    </div>
                    <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
                      urgencyStyles[watch("urgency") || analysis.urgency] || "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    }`}>
                      Urgency · {watch("urgency") || analysis.urgency}
                    </div>
                  </div>
                </div>
              )}
            </aside>
          </div>

          {submittedResult && submittedResult.simulation?.options && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 text-sm text-slate-600 dark:border-slate-800 dark:text-slate-300 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
                  <ShieldCheck className="h-5 w-5 text-emerald-500" />
                  <p className="font-semibold">Pick how you want this handled</p>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span>Category: <strong>{submittedResult.classification.category}</strong></span>
                  <span>•</span>
                  <span>Urgency: <strong>{submittedResult.classification.urgency}</strong></span>
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4 items-start">
                {submittedResult.simulation.options.map((option) => {
                  const isRecommended = option.option_id === submittedResult.simulation.recommended_option_id;
                  return (
                    <div
                      key={option.option_id}
                      className={`flex flex-col rounded-xl border p-4 shadow-sm transition hover:border-slate-400 hover:shadow-md dark:hover:border-slate-500 ${
                        isRecommended
                          ? 'border-emerald-500 ring-2 ring-emerald-300 dark:border-emerald-400 dark:ring-emerald-700 bg-emerald-50/40 dark:bg-emerald-900/30'
                          : 'border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950'
                      }`}
                      aria-label={isRecommended ? 'AI Recommended Option' : undefined}
                    >
                      <div className="flex-grow space-y-2">
                        <div className="flex items-center gap-2">
                          {/* Removed Option opt label */}
                          {isRecommended && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-200" title="AI Recommended Option">
                              <Star className="h-3 w-3 mr-1 text-emerald-500" /> Recommended
                            </span>
                          )}
                        </div>
                        <h4 className="text-base font-semibold text-slate-800 dark:text-slate-100">{option.action}</h4>
                        <div className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
                          <p className="flex justify-between"><span>Estimated cost</span><span>${parseFloat(option.estimated_cost || 0).toFixed(2)}</span></p>
                          <p className="flex justify-between"><span>Resolution time</span><span>{parseFloat(option.estimated_time || option.time_to_resolution || 0).toFixed(1)}h</span></p>
                          <p className="flex justify-between"><span>Satisfaction</span><span>{Math.round((option.resident_satisfaction_impact || 0) * 100)}%</span></p>
                        </div>
                      </div>
                      
                      {/* Details Dropdown with smooth animation */}
                      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
                        expandedOptions.has(option.option_id) ? 'max-h-[500px] opacity-100 mt-3' : 'max-h-0 opacity-0'
                      }`}>
                        <div className="rounded-lg bg-white p-3 shadow-inner dark:bg-slate-900">
                          <p className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300">What happens with this option:</p>
                          <div className="space-y-3 text-xs text-slate-600 dark:text-slate-400">
                            {/* Action steps - use LLM-generated steps if available, otherwise parse */}
                            <div>
                              <ul className="space-y-2">
                                {(option.steps && option.steps.length > 0 
                                  ? option.steps 
                                  : parseActionSteps(option.action, option.reasoning)
                                ).map((step, idx) => (
                                  <li key={idx} className="flex items-start gap-2">
                                    <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 text-xs font-semibold">
                                      {idx + 1}
                                    </span>
                                    <span className="flex-1 pt-0.5">{step}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                            
                            {/* Source documents */}
                            {option.source_doc_ids && option.source_doc_ids.length > 0 && (
                              <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                                <div className="flex items-start gap-2">
                                  <Info className="mt-0.5 h-3 w-3 flex-shrink-0 text-blue-500" />
                                  <div className="flex-1">
                                    <p className="font-semibold text-slate-700 dark:text-slate-300 mb-1">Based on policies:</p>
                                    <div className="flex flex-wrap gap-1">
                                      {[...new Set(option.source_doc_ids)].map((docId, idx) => (
                                        <span key={idx} className="inline-block px-2 py-0.5 rounded text-[10px] bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200 font-mono">
                                          {docId}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 space-y-2 flex-shrink-0">
                        <button
                          onClick={() => toggleOptionDetails(option.option_id)}
                          className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                        >
                          {expandedOptions.has(option.option_id) ? (
                            <>
                              <ChevronUp className="h-4 w-4" />
                              Hide Details
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-4 w-4" />
                              Show Details
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => handleSelectOption(option.option_id)}
                          disabled={selectingOption}
                          className="w-full inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
                        >
                          {selectingOption ? "Processing..." : "Choose this option"}
                        </button>
                      </div>
                    </div>
                  );
                })}

                <div className="flex flex-col rounded-xl border border-rose-200 bg-rose-50 p-4 shadow-sm transition hover:border-rose-300 hover:shadow-md dark:border-rose-800 dark:bg-rose-950/30 dark:hover:border-rose-600">
                  <div className="flex-grow space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-rose-500 dark:text-rose-300">Need a person?</p>
                    <h4 className="text-base font-semibold text-rose-600 dark:text-rose-200">Escalate to human support</h4>
                    <p className="text-sm text-rose-700 dark:text-rose-200/80">
                      Speak directly with our property team for personalised help. Recommended for complex or sensitive issues.
                    </p>
                  </div>
                  <button
                    onClick={() => handleSelectOption("escalate_to_human")}
                    disabled={selectingOption}
                    className="mt-4 flex-shrink-0 inline-flex items-center justify-center gap-2 rounded-lg bg-rose-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-400 disabled:opacity-60 dark:bg-rose-400 dark:text-rose-950 dark:hover:bg-rose-300"
                  >
                    <UserX className="h-4 w-4" />
                    {selectingOption ? "Processing..." : "Escalate to human"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
