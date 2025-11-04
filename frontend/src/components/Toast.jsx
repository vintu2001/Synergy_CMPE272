import { useEffect, useState } from "react";
import { CheckCircle, XCircle, X } from "lucide-react";

export default function Toast({ message, type = "success", onClose }) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300);
    }, 4000);

    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === "success" ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200";
  const textColor = type === "success" ? "text-green-800" : "text-red-800";
  const iconColor = type === "success" ? "text-green-600" : "text-red-600";

  return (
    <div
      className={`fixed top-4 right-4 z-50 flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg transition-all duration-300 ${
        isVisible ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"
      } ${bgColor}`}
    >
      {type === "success" ? (
        <CheckCircle className={`h-5 w-5 ${iconColor}`} />
      ) : (
        <XCircle className={`h-5 w-5 ${iconColor}`} />
      )}
      <p className={`text-sm font-medium ${textColor}`}>{message}</p>
      <button
        onClick={() => {
          setIsVisible(false);
          setTimeout(onClose, 300);
        }}
        className={`ml-2 ${textColor} hover:opacity-70`}
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

