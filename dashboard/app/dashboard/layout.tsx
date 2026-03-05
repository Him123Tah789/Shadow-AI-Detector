"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { logout, getRole, getOrgToken } from "@/lib/api";

const navItems = [
    { href: "/dashboard", label: "Overview", icon: "📊" },
    { href: "/dashboard/policies", label: "Policies", icon: "🛡️" },
    { href: "/dashboard/tools", label: "Tools", icon: "🧰" },
    { href: "/dashboard/audit", label: "Audit Logs", icon: "📋" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const role = getRole();
    const orgToken = getOrgToken();

    return (
        <div className="flex min-h-screen">
            {/* ── Sidebar ─────────────────────────── */}
            <aside className="w-64 bg-[#0c1222] border-r border-[#1e293b] flex flex-col">
                <div className="px-6 py-6">
                    <h1 className="text-lg font-bold text-white tracking-tight">
                        🛡️ Shadow AI
                    </h1>
                    <p className="text-xs text-slate-500 mt-1">Domain-level AI monitor</p>
                </div>

                <nav className="flex-1 px-3 space-y-1">
                    {navItems.map((item) => {
                        const active = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${active
                                        ? "bg-indigo-600/20 text-indigo-400"
                                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                                    }`}
                            >
                                <span className="text-base">{item.icon}</span>
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                {/* Org token display */}
                {orgToken && (
                    <div className="mx-3 mb-3 p-3 rounded-lg bg-[#1e293b] border border-[#334155]">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Org Token</p>
                        <p className="text-xs text-slate-300 font-mono truncate">{orgToken}</p>
                    </div>
                )}

                <div className="p-3 border-t border-[#1e293b]">
                    <div className="flex items-center justify-between px-3 py-2">
                        <span className="text-xs text-slate-500 capitalize">{role}</span>
                        <button
                            onClick={logout}
                            className="text-xs text-red-400 hover:text-red-300 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </aside>

            {/* ── Main content ───────────────────── */}
            <main className="flex-1 bg-[#0f172a] p-8 overflow-auto">
                {children}
            </main>
        </div>
    );
}
