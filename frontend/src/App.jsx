import { BrowserRouter, Routes, Route, Link, NavLink } from "react-router-dom";
import { UserProvider } from "./context/UserContext";
import ResidentSubmission from "./pages/ResidentSubmission";
import ResidentDashboard from "./pages/ResidentDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import { Home, LayoutDashboard, Shield } from "lucide-react";
import "./App.css";

function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 to-blue-50">
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/80 backdrop-blur-md shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 p-2 shadow-lg group-hover:shadow-xl transition-all">
                <Home className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Agentic Apartment Manager
                </h1>
                <p className="text-xs text-gray-500">AI-Powered Property Management</p>
              </div>
            </Link>
            <nav className="flex items-center gap-2">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md"
                      : "text-gray-600 hover:bg-gray-100"
                  }`
                }
              >
                <Home className="h-4 w-4" />
                Submit
              </NavLink>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md"
                      : "text-gray-600 hover:bg-gray-100"
                  }`
                }
              >
                <LayoutDashboard className="h-4 w-4" />
                Dashboard
              </NavLink>
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md"
                      : "text-gray-600 hover:bg-gray-100"
                  }`
                }
              >
                <Shield className="h-4 w-4" />
                Admin
              </NavLink>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <UserProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<ResidentSubmission />} />
            <Route path="/dashboard" element={<ResidentDashboard />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </Layout>
      </UserProvider>
    </BrowserRouter>
  );
}

export default App;
