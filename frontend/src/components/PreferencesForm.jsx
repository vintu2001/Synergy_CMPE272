import { useState } from "react";
import { Calendar, Clock, Phone, AlertCircle, Home } from "lucide-react";

export default function PreferencesForm({ preferences, onChange }) {
    const [expanded, setExpanded] = useState(false);

    const handleChange = (field, value) => {
        onChange({
            ...preferences,
            [field]: value,
        });
    };

    const toggleDay = (day) => {
        const current = preferences?.preferred_days || [];
        const updated = current.includes(day)
            ? current.filter((d) => d !== day)
            : [...current, day];
        handleChange("preferred_days", updated);
    };

    const toggleAvoidDay = (day) => {
        const current = preferences?.avoid_days || [];
        const updated = current.includes(day)
            ? current.filter((d) => d !== day)
            : [...current, day];
        handleChange("avoid_days", updated);
    };

    const toggleTimeSlot = (slot) => {
        const current = preferences?.preferred_time_slots || [];
        const updated = current.includes(slot)
            ? current.filter((s) => s !== slot)
            : [...current, slot];
        handleChange("preferred_time_slots", updated);
    };

    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    const timeSlots = ["Morning (8am-12pm)", "Afternoon (12pm-5pm)", "Evening (5pm-8pm)"];

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <button
                type="button"
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between text-left"
            >
                <div className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-slate-500" />
                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                        Scheduling Preferences (Optional)
                    </h3>
                </div>
                <span className="text-xs text-slate-500">
                    {expanded ? "Hide" : "Show"}
                </span>
            </button>

            {expanded && (
                <div className="mt-4 space-y-4">
                    {/* Apartment Access */}
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
                        <label className="flex items-start gap-3">
                            <input
                                type="checkbox"
                                checked={preferences?.allow_entry_when_absent || false}
                                onChange={(e) => handleChange("allow_entry_when_absent", e.target.checked)}
                                className="mt-1 h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-2 focus:ring-slate-200"
                            />
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <Home className="h-4 w-4 text-slate-500" />
                                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                                        Technician can enter when I'm not home
                                    </span>
                                </div>
                                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                    Allow service personnel to access your apartment if you're unavailable
                                </p>
                            </div>
                        </label>
                    </div>

                    {/* Preferred Days */}
                    <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                            Preferred Days
                        </p>
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                            {days.map((day) => (
                                <button
                                    key={day}
                                    type="button"
                                    onClick={() => toggleDay(day)}
                                    className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${(preferences?.preferred_days || []).includes(day)
                                            ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200"
                                            : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300"
                                        }`}
                                >
                                    {day.slice(0, 3)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Avoid Days */}
                    <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                            Days to Avoid
                        </p>
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                            {days.map((day) => (
                                <button
                                    key={day}
                                    type="button"
                                    onClick={() => toggleAvoidDay(day)}
                                    className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${(preferences?.avoid_days || []).includes(day)
                                            ? "border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200"
                                            : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300"
                                        }`}
                                >
                                    {day.slice(0, 3)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Time Slots */}
                    <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                            <Clock className="inline h-3 w-3 mr-1" />
                            Preferred Time Slots
                        </p>
                        <div className="space-y-2">
                            {timeSlots.map((slot) => (
                                <label key={slot} className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        checked={(preferences?.preferred_time_slots || []).includes(slot)}
                                        onChange={() => toggleTimeSlot(slot)}
                                        className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-2 focus:ring-slate-200"
                                    />
                                    <span className="text-sm text-slate-700 dark:text-slate-200">{slot}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Contact Before Arrival */}
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
                        <label className="flex items-start gap-3">
                            <input
                                type="checkbox"
                                checked={preferences?.contact_before_arrival !== false}
                                onChange={(e) => handleChange("contact_before_arrival", e.target.checked)}
                                className="mt-1 h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-2 focus:ring-slate-200"
                            />
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <Phone className="h-4 w-4 text-slate-500" />
                                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                                        Contact me before arrival
                                    </span>
                                </div>
                                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                    Technician will call/text 30 minutes before arriving
                                </p>
                            </div>
                        </label>
                    </div>

                    {/* Special Instructions */}
                    <div>
                        <label className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                            <AlertCircle className="h-3 w-3" />
                            Special Instructions
                        </label>
                        <textarea
                            rows={3}
                            value={preferences?.special_instructions || ""}
                            onChange={(e) => handleChange("special_instructions", e.target.value)}
                            placeholder="e.g., Dog in apartment, use side entrance, call when you arrive..."
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
