"use client";

import { useParams } from "next/navigation";
import { fetchRecoveryPlan, updateRecoveryTask } from "@/lib/api";
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

export default function RecoveryPlanDetail() {
    const params = useParams();
    const planId = Number(params.planId);
    const { data: plan, refetch } = useApi<any>(() => fetchRecoveryPlan(planId), [planId]);
    const [updating, setUpdating] = useState<number | null>(null);
    const [showConfetti, setShowConfetti] = useState(false);

    const handleToggle = async (taskId: number, currentState: boolean) => {
        setUpdating(taskId);
        try {
            const result = await updateRecoveryTask(taskId, !currentState);
            if (result.plan_progress === 1) {
                setShowConfetti(true);
                setTimeout(() => setShowConfetti(false), 3000);
            }
            refetch();
        } catch (err) {
            console.error(err);
        } finally {
            setUpdating(null);
        }
    };

    if (!plan) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-slate-500 text-sm">Loading recovery plan…</div>
            </div>
        );
    }

    const tasks = plan.tasks || [];
    const completed = tasks.filter((t: any) => t.is_completed).length;
    const total = tasks.length;
    const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

    return (
        <div className="space-y-8 max-w-3xl">
            {/* Confetti effect */}
            {showConfetti && (
                <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
                    <div className="text-center animate-bounce">
                        <div className="text-6xl">🎉</div>
                        <p className="text-2xl font-bold text-emerald-400 mt-4">All Done!</p>
                        <p className="text-slate-400 mt-2">Your {plan.platform} account is secured.</p>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex items-center gap-4">
                <span className="text-4xl">{platformIcons[plan.platform] || "🔒"}</span>
                <div>
                    <h2 className="text-2xl font-bold text-white capitalize">
                        {plan.platform} Recovery Plan
                    </h2>
                    <p className="text-slate-400 text-sm mt-1">
                        {completed} of {total} tasks completed
                    </p>
                </div>
            </div>

            {/* Progress bar */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-300">Progress</span>
                    <span className={`text-sm font-bold ${progress === 100 ? "text-emerald-400" : "text-indigo-400"}`}>
                        {progress}%
                    </span>
                </div>
                <div className="h-3 bg-[#0f172a] rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${progress === 100 ? "bg-emerald-500" : "bg-indigo-500"
                            }`}
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Tasks checklist */}
            <div className="space-y-3">
                {tasks.map((task: any) => (
                    <div
                        key={task.id}
                        className={`bg-[#1e293b] border rounded-xl p-5 transition-all ${task.is_completed
                                ? "border-emerald-800/30 bg-emerald-900/10"
                                : "border-[#334155]"
                            }`}
                    >
                        <div className="flex items-start gap-4">
                            {/* Checkbox */}
                            <button
                                onClick={() => handleToggle(task.id, task.is_completed)}
                                disabled={updating === task.id}
                                className={`mt-0.5 w-6 h-6 rounded-md border-2 flex-shrink-0 flex items-center justify-center transition-all ${task.is_completed
                                        ? "bg-emerald-600 border-emerald-600"
                                        : "border-slate-600 hover:border-emerald-500"
                                    } ${updating === task.id ? "opacity-50" : ""}`}
                            >
                                {task.is_completed && (
                                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                    </svg>
                                )}
                            </button>

                            <div className="flex-1">
                                <h4 className={`font-medium ${task.is_completed ? "text-slate-500 line-through" : "text-white"}`}>
                                    {task.title}
                                </h4>
                                {task.description && (
                                    <p className="text-sm text-slate-400 mt-1.5 leading-relaxed">
                                        {task.description}
                                    </p>
                                )}
                                <div className="flex items-center gap-3 mt-3">
                                    {task.help_url && (
                                        <a
                                            href={task.help_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
                                        >
                                            Open Settings →
                                        </a>
                                    )}
                                    {task.completed_at && (
                                        <span className="text-xs text-slate-600">
                                            Completed {new Date(task.completed_at).toLocaleDateString()}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
