"use client";

import Link from "next/link";
import { fetchBreachStatus, fetchSecurityScore } from "@/lib/api";
import { useApi } from "@/lib/hooks";

export default function PersonalDashboard() {
    const { data: breachData } = useApi<any>(fetchBreachStatus);
    const { data: scoreData } = useApi<any>(fetchSecurityScore);

    const score = scoreData?.score ?? 0;
    const grade = scoreData?.grade ?? "—";
    const gradeColors: Record<string, string> = {
        A: "text-emerald-400",
        B: "text-green-400",
        C: "text-yellow-400",
        D: "text-orange-400",
        F: "text-red-400",
    };

    const cards = [
        {
            label: "Monitored Emails",
            value: breachData?.monitored_emails?.length ?? 0,
            icon: "📧",
            color: "text-blue-400",
            bg: "bg-blue-900/20",
            border: "border-blue-800/30",
            href: "/personal/emails",
        },
        {
            label: "Total Breaches",
            value: breachData?.total_breaches ?? 0,
            icon: "🔓",
            color: "text-red-400",
            bg: "bg-red-900/20",
            border: "border-red-800/30",
            href: "/personal/breaches",
        },
        {
            label: "Unresolved",
            value: breachData?.unresolved ?? 0,
            icon: "⚠️",
            color: "text-amber-400",
            bg: "bg-amber-900/20",
            border: "border-amber-800/30",
            href: "/personal/recovery",
        },
        {
            label: "Security Score",
            value: `${score}`,
            icon: "📊",
            color: gradeColors[grade] || "text-slate-400",
            bg: "bg-emerald-900/20",
            border: "border-emerald-800/30",
            href: "/personal/score",
        },
    ];

    return (
        <div className="space-y-8 max-w-6xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Personal Dashboard</h2>
                <p className="text-slate-400 text-sm mt-1">Breach monitoring & account recovery</p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {cards.map((c) => (
                    <Link key={c.label} href={c.href}>
                        <div className={`rounded-xl p-5 ${c.bg} border ${c.border} hover:scale-[1.02] transition-transform cursor-pointer`}>
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-xs text-slate-400">{c.label}</p>
                                <span className="text-lg">{c.icon}</span>
                            </div>
                            <p className={`text-3xl font-bold ${c.color}`}>{c.value}</p>
                        </div>
                    </Link>
                ))}
            </div>

            {/* Security Score Gauge */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8">
                <h3 className="text-sm font-medium text-slate-300 mb-6">Security Score</h3>
                <div className="flex flex-col items-center">
                    <div className="relative w-48 h-48">
                        <svg viewBox="0 0 200 200" className="w-full h-full">
                            <circle cx="100" cy="100" r="80" fill="none" stroke="#1e293b" strokeWidth="16" />
                            <circle
                                cx="100" cy="100" r="80" fill="none"
                                stroke={score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444"}
                                strokeWidth="16"
                                strokeDasharray={`${(score / 100) * 502.65} 502.65`}
                                strokeLinecap="round"
                                transform="rotate(-90 100 100)"
                                className="transition-all duration-1000 ease-out"
                            />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className={`text-5xl font-bold ${gradeColors[grade] || "text-white"}`}>{grade}</span>
                            <span className="text-lg text-slate-400">{score}/100</span>
                        </div>
                    </div>

                    {/* Recommendations */}
                    {scoreData?.recommendations && (
                        <div className="mt-6 w-full max-w-md space-y-2">
                            {scoreData.recommendations.map((rec: string, i: number) => (
                                <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                    <span className="text-emerald-500 mt-0.5">→</span>
                                    <span>{rec}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Link href="/personal/emails">
                    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-emerald-700/50 transition-colors cursor-pointer text-center">
                        <span className="text-2xl">➕</span>
                        <p className="text-sm text-white mt-2 font-medium">Add Email</p>
                        <p className="text-xs text-slate-500 mt-1">Monitor for breaches</p>
                    </div>
                </Link>
                <Link href="/personal/breaches">
                    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-emerald-700/50 transition-colors cursor-pointer text-center">
                        <span className="text-2xl">🔍</span>
                        <p className="text-sm text-white mt-2 font-medium">View Breaches</p>
                        <p className="text-xs text-slate-500 mt-1">Check breach history</p>
                    </div>
                </Link>
                <Link href="/personal/recovery">
                    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-emerald-700/50 transition-colors cursor-pointer text-center">
                        <span className="text-2xl">🛠️</span>
                        <p className="text-sm text-white mt-2 font-medium">Recovery Plans</p>
                        <p className="text-xs text-slate-500 mt-1">Step-by-step guides</p>
                    </div>
                </Link>
            </div>
        </div>
    );
}
