"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { logout, getTier } from "@/lib/api";

const navItems = [
    { href: "/personal", label: "Dashboard", icon: "🏠" },
    { href: "/personal/emails", label: "Monitored Emails", icon: "📧" },
    { href: "/personal/breaches", label: "Breach History", icon: "🔓" },
    { href: "/personal/recovery", label: "Recovery Plans", icon: "🛠️" },
    { href: "/personal/score", label: "Security Score", icon: "📊" },
];

export default function PersonalLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const tier = getTier();

    return (
        <div className="flex min-h-screen">
            {/* Sidebar */}
            <aside className="w-64 bg-[#0c1222] border-r border-[#1e293b] flex flex-col">
                <div className="px-6 py-6">
                    <h1 className="text-lg font-bold text-white tracking-tight">
                        🛡️ ShieldOps
                    </h1>
                    <p className="text-xs text-emerald-500 mt-1">Breach Monitor · Personal</p>
                </div>

                <nav className="flex-1 px-3 space-y-1">
                    {navItems.map((item) => {
                        const active = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${active
                                    ? "bg-emerald-600/20 text-emerald-400"
                                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                                    }`}
                            >
                                <span className="text-base">{item.icon}</span>
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                {/* Tier Badge */}
                <div className="mx-3 mb-3 p-3 rounded-lg bg-[#1e293b] border border-[#334155]">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Plan</p>
                    <p className="text-xs text-emerald-400 font-semibold capitalize">{tier} Plan</p>
                </div>

                {/* Switch to Org */}
                <div className="mx-3 mb-3">
                    <Link
                        href="/dashboard"
                        className="block text-center text-xs text-slate-500 hover:text-indigo-400 transition-colors py-2 rounded-lg border border-[#1e293b] hover:border-indigo-800/50"
                    >
                        🏢 Switch to Org Dashboard
                    </Link>
                </div>

                <div className="p-3 border-t border-[#1e293b]">
                    <div className="flex items-center justify-between px-3 py-2">
                        <span className="text-xs text-slate-500">Personal</span>
                        <button
                            onClick={logout}
                            className="text-xs text-red-400 hover:text-red-300 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 bg-[#0f172a] p-8 overflow-auto">
                {children}
            </main>
        </div>
    );
}
