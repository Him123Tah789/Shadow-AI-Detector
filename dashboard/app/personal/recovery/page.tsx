"use client";

import Link from "next/link";
import { fetchRecoveryPlans, createRecoveryPlan, fetchPlatforms } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { useState } from "react";

const platformIcons: Record<string, string> = {
    google: "🔵",
    facebook: "🟦",
    microsoft: "🟧",
    instagram: "📸",
    apple: "🍎",
    github: "🐙",
    banking: "🏦",
};

const statusColors: Record<string, { bg: string; text: string }> = {
    pending: { bg: "bg-slate-700/50", text: "text-slate-400" },
    in_progress: { bg: "bg-amber-900/30", text: "text-amber-400" },
    completed: { bg: "bg-emerald-900/30", text: "text-emerald-400" },
};

export default function RecoveryPlansPage() {
    const { data, refetch } = useApi<any>(fetchRecoveryPlans);
    const { data: platformsData } = useApi<any>(fetchPlatforms);
    const [selectedPlatform, setSelectedPlatform] = useState("");
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState("");

    const handleCreate = async () => {
        if (!selectedPlatform) return;
        setCreating(true);
        setError("");
        try {
            await createRecoveryPlan(selectedPlatform);
            setSelectedPlatform("");
            refetch();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setCreating(false);
        }
    };

    const plans = data?.plans || [];
    const platforms = platformsData?.platforms || [];

    return (
        <div className="space-y-8 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Recovery Plans</h2>
                <p className="text-slate-400 text-sm mt-1">
                    Step-by-step guides to secure your accounts after a breach
                </p>
            </div>

            {/* Create New Plan */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                <h3 className="text-sm font-medium text-slate-300 mb-4">Create Recovery Plan</h3>
                <div className="flex gap-3">
                    <select
                        value={selectedPlatform}
                        onChange={(e) => setSelectedPlatform(e.target.value)}
                        className="flex-1 px-3 py-2.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm focus:border-emerald-500 outline-none transition appearance-none"
                    >
                        <option value="">Select a platform…</option>
                        {platforms.map((p: string) => (
                            <option key={p} value={p}>
                                {platformIcons[p] || "🔒"} {p.charAt(0).toUpperCase() + p.slice(1)}
                            </option>
                        ))}
                    </select>
                    <button
                        onClick={handleCreate}
                        disabled={!selectedPlatform || creating}
                        className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-colors disabled:opacity-50"
                    >
                        {creating ? "Creating…" : "Create Plan"}
                    </button>
                </div>
                {error && (
                    <p className="mt-3 text-red-400 text-sm">{error}</p>
                )}
            </div>

            {/* Plans List */}
            <div className="space-y-3">
                {plans.length === 0 ? (
                    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-12 text-center">
                        <span className="text-4xl">🛠️</span>
                        <p className="text-slate-400 text-sm mt-4">
                            No recovery plans yet. Create one above or start from a breach.
                        </p>
                    </div>
                ) : (
                    plans.map((plan: any) => {
                        const sc = statusColors[plan.status] || statusColors.pending;
                        const progress = Math.round(plan.progress * 100);
                        return (
                            <Link key={plan.id} href={`/personal/recovery/${plan.id}`}>
                                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-emerald-700/50 transition-colors cursor-pointer">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-3">
                                            <span className="text-2xl">{platformIcons[plan.platform] || "🔒"}</span>
                                            <div>
                                                <h3 className="text-white font-semibold capitalize">{plan.platform}</h3>
                                                <p className="text-xs text-slate-500">
                                                    Created {new Date(plan.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.text}`}>
                                            {plan.status.replace("_", " ")}
                                        </span>
                                    </div>

                                    {/* Progress bar */}
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 h-2 bg-[#0f172a] rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all duration-500 ${progress === 100 ? "bg-emerald-500" : "bg-indigo-500"
                                                    }`}
                                                style={{ width: `${progress}%` }}
                                            />
                                        </div>
                                        <span className="text-xs text-slate-400 w-10 text-right">{progress}%</span>
                                    </div>
                                </div>
                            </Link>
                        );
                    })
                )}
            </div>
        </div>
    );
}
