import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Link, NavLink, useLocation } from "react-router-dom";
import { UserProvider, useUser } from "./context/UserContext";
import ResidentSubmission from "./pages/ResidentSubmission";
import ResidentDashboard from "./pages/ResidentDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import Home from "./pages/Home";
import { Sun, Moon, LayoutDashboard, Shield, Home as HomeIcon, FileText } from "lucide-react";
import "./App.css";

function Layout({ children }) {
  const location = useLocation();
  const { residentId } = useUser();
  const isAdminRoute = location.pathname === "/admin";
  const isResidentRoute = location.pathname === "/resident" || location.pathname === "/dashboard";
  const isHomePage = location.pathname === "/";
  const adminKey = typeof window !== "undefined" ? localStorage.getItem("admin_api_key") : null;
  const [theme, setTheme] = useState(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem("theme") : null;
    if (stored === "dark" || stored === "light") return stored;
    const prefersDark =
      typeof window !== "undefined" && window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)").matches : false;
    return prefersDark ? "dark" : "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    if (typeof window !== "undefined") {
      localStorage.setItem("theme", theme);
    }
    root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme === "dark" ? "dark" : "light";
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-50">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur-md shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        <div className="w-full px-4 py-4 sm:px-6 lg:px-10">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="rounded-lg bg-slate-900 p-2 text-white shadow-md dark:bg-slate-100 dark:text-slate-900">
                <HomeIcon className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                  SAM
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-300">AI-assisted resident and admin workspace</p>
              </div>
            </Link>
            <nav className="flex items-center gap-1 sm:gap-2">
              <button
                onClick={toggleTheme}
                className="rounded-lg p-2 text-slate-600 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-200 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-slate-700"
                aria-label="Toggle theme"
              >
                {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
              
              {!isHomePage && (
                <>
                  <NavLink
                    to="/"
                    className={({ isActive }) =>
                      `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                        isActive ? "bg-slate-900 text-white shadow-sm dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                      }`
                    }
                  >
                    <HomeIcon className="h-4 w-4" />
                    Home
                  </NavLink>

                  {/* Show resident navigation only if logged in as resident or on resident pages */}
                  {(residentId || isResidentRoute) && !isAdminRoute && (
                    <>
                      <NavLink
                        to="/resident"
                        className={({ isActive }) =>
                          `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                            isActive ? "bg-slate-900 text-white shadow-sm dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                          }`
                        }
                      >
                        <FileText className="h-4 w-4" />
                        Resident Form
                      </NavLink>
                      <NavLink
                        to="/dashboard"
                        className={({ isActive }) =>
                          `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                            isActive ? "bg-slate-900 text-white shadow-sm dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                          }`
                        }
                      >
                        <LayoutDashboard className="h-4 w-4" />
                        Resident Dashboard
                      </NavLink>
                    </>
                  )}

                  {/* Show admin navigation only if logged in as admin or on admin page */}
                  {(adminKey || isAdminRoute) && !isResidentRoute && (
                    <NavLink
                      to="/admin"
                      className={({ isActive }) =>
                        `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                          isActive ? "bg-slate-900 text-white shadow-sm dark:bg-slate-100 dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                        }`
                      }
                    >
                      <Shield className="h-4 w-4" />
                      Admin Console
                    </NavLink>
                  )}
                </>
              )}
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1 w-full">{children}</main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <UserProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/resident" element={<ResidentSubmission />} />
            <Route path="/dashboard" element={<ResidentDashboard />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </Layout>
      </UserProvider>
    </BrowserRouter>
  );
}

export default App;
