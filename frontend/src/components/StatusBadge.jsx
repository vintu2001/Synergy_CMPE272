const styles = {
  Submitted: "bg-blue-100 text-blue-800",
  Processing: "bg-yellow-100 text-yellow-800",
  "In Progress": "bg-indigo-100 text-indigo-800",
  Resolved: "bg-green-100 text-green-800",
  Escalated: "bg-red-100 text-red-800",
};

export default function StatusBadge({ status }) {
  const cls = styles[status] || "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}


