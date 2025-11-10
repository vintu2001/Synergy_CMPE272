const styles = {
  Submitted: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200",
  Processing: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
  "In Progress": "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200",
  Resolved: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200",
  Escalated: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200",
};

export default function StatusBadge({ status }) {
  const cls = styles[status] || "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200";
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}



