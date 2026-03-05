"use client";

import { fetchSecurityScore, fetchScoreHistory } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function SecurityScorePage() {
    const { data: scoreData } = useApi<any>(fetchSecurityScore);
    const { data: historyData } = useApi<any>(() => fetchScoreHistory(12));

    const score = scoreData?.score ?? 0;
    const grade = scoreData?.grade ?? "—";
    const breakdown = scoreData?.breakdown || {};
    const recommendations = scoreData?.recommendations || [];
    const history = historyData?.history || [];

    const gradeColors: Record<string, { main: string; ring: string }> = {
        A: { main: "text-emerald-400", ring: "#10b981" },
        B: { main: "text-green-400", ring: "#22c55e" },
        C: { main: "text-yellow-400", ring: "#eab308" },
        D: { main: "text-orange-400", ring: "#f97316" },
        F: { main: "text-red-400", ring: "#ef4444" },
    };
    const gc = gradeColors[grade] || gradeColors.C;

    const breakdownItems = [
        { label: "Emails Monitored", value: breakdown.emails_monitored ?? 0, icon: "📧" },
        { label: "Total Breaches", value: breakdown.total_breaches ?? 0, icon: "🔓" },
        { label: "Recoveries Done", value: breakdown.breaches_with_recovery ?? 0, icon: "✅" },
        { label: "Tasks Completed", value: `${breakdown.tasks_completed ?? 0}/${breakdown.tasks_total ?? 0}`, icon: "📋" },
    ];

    return (
        <div className="space-y-8 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Security Score</h2>
                <p className="text-slate-400 text-sm mt-1">
                    Your overall security posture across monitored accounts
                </p>
            </div>

            {/* Score Gauge + Grade */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8">
                <div className="flex flex-col md:flex-row items-center gap-8">
                    {/* SVG Gauge */}
                    <div className="relative w-52 h-52 flex-shrink-0">
                        <svg viewBox="0 0 200 200" className="w-full h-full">
                            <circle cx="100" cy="100" r="80" fill="none" stroke="#1e293b" strokeWidth="14" />
                            <circle
                                cx="100" cy="100" r="80" fill="none"
                                stroke={gc.ring}
                                strokeWidth="14"
                                strokeDasharray={`${(score / 100) * 502.65} 502.65`}
                                strokeLinecap="round"
                                transform="rotate(-90 100 100)"
                                className="transition-all duration-1000 ease-out"
                            />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className={`text-5xl font-bold ${gc.main}`}>{grade}</span>
                            <span className="text-xl text-slate-400 mt-1">{score}/100</span>
                        </div>
                    </div>

                    {/* Breakdown Cards */}
                    <div className="flex-1 grid grid-cols-2 gap-4 w-full">
                        {breakdownItems.map((item) => (
                            <div key={item.label} className="bg-[#0f172a] rounded-lg p-4 border border-[#334155]">
                                <div className="flex items-center gap-2 mb-1">
                                    <span>{item.icon}</span>
                                    <span className="text-xs text-slate-500">{item.label}</span>
                                </div>
                                <p className="text-lg font-bold text-white">{item.value}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Score History Chart */}
            {history.length > 1 && (
                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-slate-300 mb-4">Score History</h3>
                    <ResponsiveContainer width="100%" height={220}>
                        <LineChart data={history.map((h: any) => ({
                            ...h,
                            date: new Date(h.calculated_at).toLocaleDateString("en", { month: "short", day: "numeric" }),
                        }))}>
                            <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} />
                            <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} />
                            <Tooltip
                                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, color: "#e2e8f0" }}
                                formatter={(value: any) => [`${value}/100`, "Score"]}
                            />
                            <Line type="monotone" dataKey="score" stroke={gc.ring} strokeWidth={2.5} dot={{ fill: gc.ring, r: 4 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Recommendations */}
            {recommendations.length > 0 && (
                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-slate-300 mb-4">💡 Recommendations</h3>
                    <div className="space-y-3">
                        {recommendations.map((rec: string, i: number) => (
                            <div key={i} className="flex items-start gap-3 bg-[#0f172a] rounded-lg p-4 border border-[#334155]">
                                <span className="text-emerald-500 mt-0.5 text-lg">→</span>
                                <span className="text-sm text-slate-300">{rec}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
