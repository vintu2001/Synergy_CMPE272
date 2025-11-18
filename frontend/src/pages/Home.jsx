import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Shield, User, Building2, KeyRound, Sparkles, BarChart3, Zap, MessageSquare, CheckCircle2, Clock, TrendingUp } from "lucide-react";
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
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 flex items-center py-12 px-4">
      <div className="w-full max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-[1.2fr_1fr] gap-8 lg:gap-12 items-center">
          {/* Left Side - Hero & Details */}
          <div className="space-y-6">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-1.5 text-sm font-semibold text-white shadow-lg dark:bg-slate-200 dark:text-slate-900 mb-4">
                <Building2 className="h-4 w-4" />
                Synergy Apartment Portal
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-3">
                AI-Powered Apartment Management
              </h1>
              <p className="text-base md:text-lg text-slate-600 dark:text-slate-300 mb-6">
                Intelligent service request management with AI-driven classification, risk prediction, and automated resolution options.
              </p>
            </div>

            {/* Key Features - Compact */}
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-emerald-100 p-2.5 dark:bg-emerald-900/30 flex-shrink-0">
                  <Sparkles className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-0.5">
                    AI-Powered Classification
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Automatically categorizes requests and determines urgency using machine learning.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-blue-100 p-2.5 dark:bg-blue-900/30 flex-shrink-0">
                  <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-0.5">
                    Risk Prediction
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Identifies recurring issues and predicts risks to prioritize urgent matters.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-purple-100 p-2.5 dark:bg-purple-900/30 flex-shrink-0">
                  <Zap className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-0.5">
                    Automated Solutions
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Generates resolution options with cost, time, and satisfaction estimates.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-amber-100 p-2.5 dark:bg-amber-900/30 flex-shrink-0">
                  <MessageSquare className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-0.5">
                    Real-Time Communication
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Admins can update statuses and add comments for transparent communication.
                  </p>
                </div>
              </div>
            </div>

            {/* Stats - Compact */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
              <div className="text-center">
                <div className="text-xl font-bold text-slate-900 dark:text-white">RAG</div>
                <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">Enhanced</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-slate-900 dark:text-white">5+</div>
                <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">Categories</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-slate-900 dark:text-white">3</div>
                <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">Options</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-slate-900 dark:text-white">35+</div>
                <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">Policy Docs</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-slate-900 dark:text-white">24/7</div>
                <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">Available</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-slate-900 dark:text-white">95%</div>
                <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">Accuracy</div>
              </div>
            </div>
          </div>

          {/* Right Side - Login Forms */}
          <div className="w-full">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">
                {isAdminView ? "Admin Console" : "Resident Portal"}
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {isAdminView
                  ? "Manage requests, update statuses, and communicate with residents."
                  : "Submit service requests and track progress in real-time."}
              </p>
            </div>

        {!isAdminView ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-lg dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-full bg-slate-900 p-3 text-white shadow-md dark:bg-slate-100 dark:text-slate-900">
                <User className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Resident Login</h2>
                <p className="text-sm text-slate-500 dark:text-slate-300">
                  Enter your details to access the resident portal
                </p>
              </div>
            </div>

            <form className="space-y-4" onSubmit={handleResidentSubmit}>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-200">Your name</label>
                <input
                  className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                  placeholder="e.g., Jordan Smith"
                  value={residentName}
                  onChange={(e) => setResidentName(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-200">Apartment number</label>
                <input
                  className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-800"
                  placeholder="e.g., RES_1001"
                  value={apartmentNumber}
                  onChange={(e) => setApartmentNumber(e.target.value)}
                />
              </div>
              {residentError && <p className="text-sm text-red-500">{residentError}</p>}
              <button
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-300 active:scale-[0.99] dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
              >
                Continue to Resident Portal
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <div className="mt-6 text-center">
              <button
                onClick={() => setIsAdminView(true)}
                className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition"
              >
                Are you an admin? <span className="font-semibold">Login as Admin instead</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-lg dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-full bg-purple-600 p-3 text-white shadow-md dark:bg-purple-400 dark:text-slate-900">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Admin Login</h2>
                <p className="text-sm text-slate-500 dark:text-slate-300">
                  Enter your credentials to access the admin console
                </p>
              </div>
            </div>

            <form className="space-y-4" onSubmit={handleAdminSubmit}>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-200">Admin password</label>
                <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm focus-within:border-slate-500 focus-within:ring-2 focus-within:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:focus-within:border-slate-400 dark:focus-within:ring-slate-800">
                  <KeyRound className="h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <input
                    type="password"
                    className="w-full border-0 bg-transparent text-sm text-slate-900 focus:outline-none dark:text-slate-100"
                    placeholder="Enter admin access password"
                    value={adminKey}
                    onChange={(e) => setAdminKey(e.target.value)}
                  />
                </div>
              </div>
              {adminError && <p className="text-sm text-red-500">{adminError}</p>}
              <button
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200 active:scale-[0.99] dark:bg-purple-400 dark:text-slate-900 dark:hover:bg-purple-300"
              >
                Enter Admin Console
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
              Tip: The password corresponds to your admin API key.
            </p>

            <div className="mt-6 text-center">
              <button
                onClick={() => setIsAdminView(false)}
                className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition"
              >
                Not an admin? <span className="font-semibold">Login as Resident instead</span>
              </button>
            </div>
          </div>
        )}
          </div>
        </div>
      </div>
    </div>
  );
}

