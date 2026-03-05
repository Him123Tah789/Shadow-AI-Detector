"use client";

import { fetchSummary, fetchTopTools, fetchTrends, fetchRisk } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    LineChart, Line, PieChart, Pie, Cell,
} from "recharts";

const COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#818cf8", "#6ee7b7", "#f59e0b", "#f87171"];

export default function OverviewPage() {
    const { data: summary } = useApi<any>(fetchSummary);
    const { data: topTools } = useApi<any[]>(() => fetchTopTools(30));
    const { data: trends } = useApi<any[]>(() => fetchTrends(30));
    const { data: risk } = useApi<any[]>(fetchRisk);

    const cards = [
        { label: "Total Events (30d)", value: summary?.total ?? "—", color: "text-indigo-400", bg: "bg-indigo-900/20", border: "border-indigo-800/30" },
        { label: "Warnings Issued", value: summary?.warned ?? "—", color: "text-amber-400", bg: "bg-amber-900/20", border: "border-amber-800/30" },
        { label: "Blocked Attempts", value: summary?.blocked ?? "—", color: "text-red-400", bg: "bg-red-900/20", border: "border-red-800/30" },
        { label: "Unique Users", value: summary?.unique_users ?? "—", color: "text-emerald-400", bg: "bg-emerald-900/20", border: "border-emerald-800/30" },
    ];

    return (
        <div className="space-y-8 max-w-6xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">Overview</h2>
                    <p className="text-slate-400 text-sm mt-1">Last 30 days of AI usage across your organization</p>
                </div>
                <button
                    onClick={() => {
                        const token = localStorage.getItem("token") || "";
                        window.open(`http://localhost:8000/api/v1/analytics/export?token=${token}`, "_blank");
                    }}
                    className="flex items-center gap-2 bg-[#1e293b] hover:bg-[#334155] border border-[#334155] text-slate-300 px-4 py-2 flex items-center gap-2 rounded-lg text-sm font-medium transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Export CSV
                </button>
            </div>

            {/* KPI cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {cards.map((c) => (
                    <div key={c.label} className={`rounded-xl p-5 ${c.bg} border ${c.border}`}>
                        <p className="text-xs text-slate-400 mb-1">{c.label}</p>
                        <p className={`text-3xl font-bold ${c.color}`}>{c.value}</p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Tools bar chart */}
                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-slate-300 mb-4">Top AI Tools</h3>
                    {topTools && topTools.length > 0 ? (
                        <ResponsiveContainer width="100%" height={260}>
                            <BarChart data={topTools} layout="vertical">
                                <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} />
                                <YAxis dataKey="name" type="category" width={100} tick={{ fill: "#94a3b8", fontSize: 12 }} />
                                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, color: "#e2e8f0" }} />
                                <Bar dataKey="count" fill="#6366f1" radius={[0, 6, 6, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <p className="text-slate-500 text-sm py-12 text-center">No data yet. Events will appear here.</p>
                    )}
                </div>

                {/* Trends line chart */}
                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-slate-300 mb-4">Usage Trend</h3>
                    {trends && trends.length > 0 ? (
                        <ResponsiveContainer width="100%" height={260}>
                            <LineChart data={trends}>
                                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 10 }} />
                                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, color: "#e2e8f0" }} />
                                <Line type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <p className="text-slate-500 text-sm py-12 text-center">No trend data yet.</p>
                    )}
                </div>
            </div>

            {/* Risk pie chart */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                <h3 className="text-sm font-medium text-slate-300 mb-4">Risk by Category</h3>
                <div className="flex flex-col md:flex-row items-center gap-8">
                    {risk && risk.length > 0 ? (
                        <>
                            <ResponsiveContainer width={220} height={220}>
                                <PieChart>
                                    <Pie data={risk} dataKey="event_count" nameKey="category" cx="50%" cy="50%" innerRadius={50} outerRadius={90}>
                                        {risk.map((_: any, i: number) => (
                                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, color: "#e2e8f0" }} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="space-y-2">
                                {risk.map((r: any, i: number) => (
                                    <div key={r.category} className="flex items-center gap-3">
                                        <span className="w-3 h-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                                        <span className="text-sm text-slate-300 capitalize">{r.category}</span>
                                        <span className="text-xs text-slate-500">{r.event_count} events · risk {r.score}</span>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <p className="text-slate-500 text-sm py-8 text-center w-full">No risk data yet.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
