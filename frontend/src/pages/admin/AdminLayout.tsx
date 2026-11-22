import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";

const links = [
  { to: "/admin/subjects", label: "Subjects & Topics" },
  { to: "/admin/questions", label: "Questions" },
  { to: "/admin/templates", label: "Exam Templates" },
  { to: "/admin/attempts", label: "Attempts" },
  { to: "/admin/testtakers", label: "Test-takers" },
];

export function AdminLayout() {
  const navigate = useNavigate();

  async function logout() {
    await api.post("/auth/admin/logout");
    navigate("/admin/login");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex border-b border-slate-200 bg-white px-6">
        <div className="flex gap-1 py-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm font-medium ${isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
        <div className="ml-auto flex items-center">
          <button onClick={logout} className="text-sm text-slate-400 hover:text-slate-600">
            Log out
          </button>
        </div>
      </div>
      <div className="mx-auto max-w-5xl px-6 py-8">
        <Outlet />
      </div>
    </div>
  );
}
