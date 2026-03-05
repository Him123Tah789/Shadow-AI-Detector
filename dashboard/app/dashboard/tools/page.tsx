"use client";

import { fetchTools } from "@/lib/api";
import { useApi } from "@/lib/hooks";

const categoryColors: Record<string, string> = {
    chat: "bg-blue-900/30 text-blue-400 border-blue-800/30",
    code: "bg-purple-900/30 text-purple-400 border-purple-800/30",
    image: "bg-pink-900/30 text-pink-400 border-pink-800/30",
    file: "bg-teal-900/30 text-teal-400 border-teal-800/30",
};

const riskColor = (score: number) => {
    if (score <= 4) return "text-emerald-400";
    if (score <= 6) return "text-amber-400";
    return "text-red-400";
};

export default function ToolsPage() {
    const { data: tools, loading } = useApi<any[]>(fetchTools);

    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">AI Tool Catalog</h2>
                <p className="text-slate-400 text-sm mt-1">Known AI tools tracked by the system</p>
            </div>

            <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-[#334155]">
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Name</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Domain</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Category</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Risk Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && (
                            <tr><td colSpan={4} className="px-5 py-8 text-center text-slate-500">Loading…</td></tr>
                        )}
                        {tools?.map((t: any) => (
                            <tr key={t.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/30 transition-colors">
                                <td className="px-5 py-3 text-slate-200 font-medium">{t.name}</td>
                                <td className="px-5 py-3 font-mono text-xs text-slate-400">{t.domain}</td>
                                <td className="px-5 py-3">
                                    <span className={`text-xs px-2.5 py-1 rounded-full border capitalize ${categoryColors[t.category] || "text-slate-400"}`}>
                                        {t.category}
                                    </span>
                                </td>
                                <td className={`px-5 py-3 font-bold tabular-nums ${riskColor(t.base_risk_score)}`}>{t.base_risk_score}/10</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
