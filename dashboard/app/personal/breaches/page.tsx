"use client";

import Link from "next/link";
import { fetchBreachStatus, createRecoveryPlan } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { useState } from "react";

const severityColors: Record<string, { bg: string; text: string; border: string }> = {
    critical: { bg: "bg-red-900/30", text: "text-red-400", border: "border-red-800/30" },
    high: { bg: "bg-orange-900/30", text: "text-orange-400", border: "border-orange-800/30" },
    medium: { bg: "bg-yellow-900/30", text: "text-yellow-400", border: "border-yellow-800/30" },
    low: { bg: "bg-blue-900/30", text: "text-blue-400", border: "border-blue-800/30" },
};

export default function BreachesPage() {
    const { data } = useApi<any>(fetchBreachStatus);
    const [creating, setCreating] = useState<number | null>(null);
    const [message, setMessage] = useState("");

    const handleStartRecovery = async (breach: any) => {
        setCreating(breach.id);
        setMessage("");
        try {
            // Use source_name as platform (lowercase)
            const platform = breach.source_name.toLowerCase();
            await createRecoveryPlan(platform, breach.id);
            setMessage(`Recovery plan created for ${breach.source_name}!`);
        } catch (err: any) {
            setMessage(err.message);
        } finally {
            setCreating(null);
        }
    };

    const allBreaches: any[] = [];
    if (data?.monitored_emails) {
        for (const em of data.monitored_emails) {
            for (const b of em.breaches || []) {
                allBreaches.push({ ...b, email_masked: em.email_masked });
            }
        }
    }
    // Sort by discovered_at descending
    allBreaches.sort((a, b) => new Date(b.discovered_at).getTime() - new Date(a.discovered_at).getTime());

    return (
        <div className="space-y-8 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Breach History</h2>
                <p className="text-slate-400 text-sm mt-1">
                    All breaches discovered across your monitored emails
                </p>
            </div>

            {message && (
                <div className="bg-emerald-900/20 border border-emerald-800/30 rounded-lg px-4 py-3 text-sm text-emerald-400">
                    {message}
                    {message.includes("created") && (
                        <Link href="/personal/recovery" className="ml-2 underline hover:text-emerald-300">
                            View Plans →
                        </Link>
                    )}
                </div>
            )}

            {/* Stats bar */}
            <div className="flex gap-4">
                <div className="bg-[#1e293b] border border-[#334155] rounded-lg px-4 py-3">
                    <p className="text-xs text-slate-500">Total</p>
                    <p className="text-lg font-bold text-white">{data?.total_breaches ?? 0}</p>
                </div>
                <div className="bg-[#1e293b] border border-[#334155] rounded-lg px-4 py-3">
                    <p className="text-xs text-slate-500">Unresolved</p>
                    <p className="text-lg font-bold text-amber-400">{data?.unresolved ?? 0}</p>
                </div>
            </div>

            {/* Breach Timeline */}
            <div className="space-y-4">
                {allBreaches.length === 0 ? (
                    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-12 text-center">
                        <span className="text-4xl">✅</span>
                        <p className="text-slate-400 text-sm mt-4">
                            No breaches found. Run a check on your monitored emails to scan.
                        </p>
                    </div>
                ) : (
                    allBreaches.map((breach: any) => {
                        const sev = severityColors[breach.severity] || severityColors.medium;
                        return (
                            <div key={breach.id} className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-4">
                                        <div className="text-2xl mt-1">🔓</div>
                                        <div>
                                            <h3 className="text-white font-semibold text-lg">{breach.source_name}</h3>
                                            <p className="text-xs text-slate-500 mt-1">{breach.email_masked}</p>

                                            <div className="flex flex-wrap items-center gap-2 mt-3">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${sev.bg} ${sev.text} border ${sev.border}`}>
                                                    {breach.severity}
                                                </span>
                                                {breach.breach_date && (
                                                    <span className="text-xs text-slate-500">
                                                        Breached: {breach.breach_date}
                                                    </span>
                                                )}
                                                <span className="text-xs text-slate-600">
                                                    Found: {new Date(breach.discovered_at).toLocaleDateString()}
                                                </span>
                                            </div>

                                            {breach.data_classes && breach.data_classes.length > 0 && (
                                                <div className="flex flex-wrap gap-1.5 mt-3">
                                                    {breach.data_classes.map((dc: string) => (
                                                        <span key={dc} className="px-2 py-0.5 rounded bg-slate-800 text-xs text-slate-400">
                                                            {dc}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => handleStartRecovery(breach)}
                                        disabled={creating === breach.id}
                                        className="px-4 py-2 rounded-lg bg-emerald-600/20 text-emerald-400 text-sm font-medium border border-emerald-800/30 hover:bg-emerald-600/30 transition-colors disabled:opacity-50 whitespace-nowrap"
                                    >
                                        {creating === breach.id ? "Creating…" : "Start Recovery →"}
                                    </button>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
