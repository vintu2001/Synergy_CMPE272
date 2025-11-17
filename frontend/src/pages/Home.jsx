import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Shield, User, Building2, KeyRound } from "lucide-react";
import { useUser } from "../context/UserContext";

export default function Home() {
  const navigate = useNavigate();
  const { setResidentProfile } = useUser();

  const [isAdminView, setIsAdminView] = useState(false);

  const [residentName, setResidentName] = useState("");
  const [apartmentNumber, setApartmentNumber] = useState("");
  const [residentError, setResidentError] = useState("");

  const [adminKey, setAdminKey] = useState("");
  const [adminError, setAdminError] = useState("");

  const handleResidentSubmit = (e) => {
    e.preventDefault();
    if (!residentName.trim() || !apartmentNumber.trim()) {
      setResidentError("Please provide both your name and apartment number.");
      return;
    }
    setResidentProfile({
      id: apartmentNumber.trim(),
      name: residentName.trim(),
    });
    setResidentError("");
    navigate("/resident");
  };

  const handleAdminSubmit = (e) => {
    e.preventDefault();
    if (!adminKey.trim()) {
      setAdminError("Please enter the admin password.");
      return;
    }
    localStorage.setItem("admin_api_key", adminKey.trim());
    setAdminError("");
    navigate("/admin");
  };

  return (
    <div className="relative w-full min-h-screen flex items-center justify-center py-12 px-4">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('/apartment-bg.webp')" }}
      />
      {/* Dark overlay + slight blur for readability */}
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-[2px]" />

      <div className="relative z-10 w-full max-w-6xl grid gap-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] items-center">
        {/* Left hero section (only on lg+) */}
        <div className="hidden lg:flex flex-col gap-6 text-slate-50">
          <p className="inline-flex items-center gap-2 rounded-full bg-slate-900/70 px-4 py-2 text-xs font-semibold shadow-lg">
            <Building2 className="h-4 w-4" />
            Synergy Apartment Management
          </p>

          <h1 className="text-4xl font-semibold leading-tight">
            Synergy Agentic Apartment Manager
          </h1>

          <p className="inline-block text-lg md:text-xl text-slate-100/90 max-w-xl bg-slate-900/75 px-4 py-3 rounded-xl shadow-lg backdrop-blur-sm">
            Synergy is is an autonomous, AI-driven system that functions as a proactive digital property manager for apartment complexes.
            that connects residents to staff through a streamlined portal. 
            Residents may easily submit and track requests, that will autonomously executes actions with explainability and observability for managers.
          </p>

          <div className="flex flex-wrap gap-4 text-sm text-slate-100/90">
            <div className="inline-flex items-center gap-2 rounded-xl bg-slate-900/70 px-3 py-2">
              <User className="h-4 w-4" />
              <span>Resident-first service requests</span>
            </div>
            <div className="inline-flex items-center gap-2 rounded-xl bg-slate-900/70 px-3 py-2">
              <Shield className="h-4 w-4" />
              <span>Secure admin controls</span>
            </div>
          </div>
        </div>

        {/* Right login card */}
        <div className="w-full max-w-md ml-auto">
          <div className="mb-6 text-center lg:text-left">
            <p className="inline-flex items-center gap-2 rounded-full bg-slate-900/80 px-3 py-1 text-xs font-semibold text-slate-100 shadow-lg">
              <Building2 className="h-4 w-4" />
              Synergy Resident Portal
            </p>
            <h2 className="mt-4 text-3xl font-semibold text-white">
              {isAdminView ? "Admin Login" : "Resident Login"}
            </h2>
            <p className="mt-3 text-sm text-slate-200">
              {isAdminView
                ? "Use your admin key to manage escalations and building services."
                : "Enter your details to submit new requests and track ongoing issues."}
            </p>
          </div>

          {!isAdminView ? (
            <div className="rounded-2xl bg-white/95 p-8 shadow-2xl backdrop-blur-sm dark:bg-slate-900/95">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-slate-50 dark:bg-slate-100 dark:text-slate-900">
                  <User className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                    Resident Login
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-300">
                    Enter your details to access the resident portal.
                  </p>
                </div>
              </div>

              <form className="space-y-4" onSubmit={handleResidentSubmit}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Your name
                  </label>
                  <input
                    type="text"
                    value={residentName}
                    onChange={(e) => setResidentName(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-50"
                    placeholder="e.g. Alex Chen"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Apartment number
                  </label>
                  <input
                    type="text"
                    value={apartmentNumber}
                    onChange={(e) => setApartmentNumber(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-50"
                    placeholder="e.g. 4B"
                  />
                </div>

                {residentError && (
                  <p className="text-sm text-rose-500">{residentError}</p>
                )}

                <button
                  type="submit"
                  className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-50 shadow-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-900/0 dark:bg-slate-100 dark:text-slate-900"
                >
                  Continue as Resident
                  <ArrowRight className="h-4 w-4" />
                </button>
              </form>

              <div className="mt-6 border-t border-slate-100 pt-4 text-center dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAdminView(true)}
                  className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100 transition"
                >
                  Are you an admin?{" "}
                  <span className="font-semibold">Login as Admin instead</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl bg-white/95 p-8 shadow-2xl backdrop-blur-sm dark:bg-slate-900/95">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500 text-white shadow-md dark:bg-amber-400 dark:text-slate-900">
                  <Shield className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                    Admin Console
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-300">
                    Enter your admin key to access escalations and analytics.
                  </p>
                </div>
              </div>

              <form className="space-y-4" onSubmit={handleAdminSubmit}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Admin key
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                      <KeyRound className="h-4 w-4" />
                    </span>
                    <input
                      type="password"
                      value={adminKey}
                      onChange={(e) => setAdminKey(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 bg-white px-9 py-2 text-sm text-slate-900 shadow-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-amber-300 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-50"
                      placeholder="Enter admin key"
                    />
                  </div>
                </div>

                {adminError && (
                  <p className="text-sm text-rose-500">{adminError}</p>
                )}

                <button
                  type="submit"
                  className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-amber-500 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-300 focus:ring-offset-2 focus:ring-offset-slate-900/0"
                >
                  Sign in as Admin
                  <ArrowRight className="h-4 w-4" />
                </button>
              </form>

              <div className="mt-6 border-t border-slate-100 pt-4 text-center dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAdminView(false)}
                  className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100 transition"
                >
                  Not an admin?{" "}
                  <span className="font-semibold">
                    Login as Resident instead
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
