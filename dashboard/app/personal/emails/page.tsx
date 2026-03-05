"use client";

import { useState } from "react";
import { addMonitoredEmail, fetchMonitoredEmails, removeMonitoredEmail, runBreachCheck } from "@/lib/api";
import { useApi } from "@/lib/hooks";

export default function EmailsPage() {
    const { data, refetch } = useApi<any>(fetchMonitoredEmails);
    const [email, setEmail] = useState("");
    const [label, setLabel] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);
    const [checking, setChecking] = useState<number | null>(null);

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess("");
        setLoading(true);
        try {
            await addMonitoredEmail(email, label || undefined);
            setEmail("");
            setLabel("");
            setSuccess("Email added! Running initial breach check...");
            refetch();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRemove = async (id: number) => {
        if (!confirm("Remove this email from monitoring?")) return;
        try {
            await removeMonitoredEmail(id);
            refetch();
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleCheck = async (id: number) => {
        setChecking(id);
        try {
            const result = await runBreachCheck(id);
            setSuccess(result.message);
            refetch();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setChecking(null);
        }
    };

    const emails = data?.emails || [];
    const used = data?.used || 0;
    const maxEmails = data?.max_emails || 1;
    const tier = data?.tier || "free";

    return (
        <div className="space-y-8 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Monitored Emails</h2>
                <p className="text-slate-400 text-sm mt-1">
                    Add emails to monitor for data breaches
                </p>
            </div>

            {/* Tier indicator */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 flex items-center justify-between">
                <div>
                    <span className="text-sm text-slate-300">
                        {used} of {maxEmails} email{maxEmails > 1 ? "s" : ""} used
                    </span>
                    <span className="ml-2 text-xs text-emerald-500 capitalize">({tier} plan)</span>
                </div>
                <div className="w-32 h-2 bg-[#0f172a] rounded-full overflow-hidden">
                    <div
                        className="h-full bg-emerald-500 rounded-full transition-all"
                        style={{ width: `${(used / maxEmails) * 100}%` }}
                    />
                </div>
            </div>

            {/* Add Email Form */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                <h3 className="text-sm font-medium text-slate-300 mb-4">Add Email to Monitor</h3>
                <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-3">
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="you@example.com"
                        className="flex-1 px-3 py-2.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm placeholder:text-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                    />
                    <input
                        type="text"
                        value={label}
                        onChange={(e) => setLabel(e.target.value)}
                        placeholder="Label (optional)"
                        className="sm:w-40 px-3 py-2.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm placeholder:text-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                    />
                    <button
                        type="submit"
                        disabled={loading || used >= maxEmails}
                        className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-colors disabled:opacity-50"
                    >
                        {loading ? "Adding…" : "Start Monitoring"}
                    </button>
                </form>

                {error && (
                    <p className="mt-3 text-red-400 text-sm bg-red-900/20 border border-red-800/30 rounded-lg px-3 py-2">{error}</p>
                )}
                {success && (
                    <p className="mt-3 text-emerald-400 text-sm bg-emerald-900/20 border border-emerald-800/30 rounded-lg px-3 py-2">{success}</p>
                )}
            </div>

            {/* Email List */}
            <div className="space-y-3">
                {emails.length === 0 ? (
                    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-12 text-center">
                        <span className="text-4xl">📧</span>
                        <p className="text-slate-400 text-sm mt-4">No emails monitored yet. Add one above to get started.</p>
                    </div>
                ) : (
                    emails.map((em: any) => (
                        <div key={em.id} className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`w-3 h-3 rounded-full ${em.is_active ? "bg-emerald-500" : "bg-slate-600"}`} />
                                <div>
                                    <p className="text-sm text-white font-medium">{em.email_masked}</p>
                                    <div className="flex items-center gap-3 mt-1">
                                        {em.label && <span className="text-xs text-slate-500">{em.label}</span>}
                                        <span className="text-xs text-slate-600">
                                            Last checked: {em.last_checked ? new Date(em.last_checked).toLocaleDateString() : "Never"}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                {em.breach_count > 0 && (
                                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-900/30 text-red-400 border border-red-800/30">
                                        {em.breach_count} breach{em.breach_count > 1 ? "es" : ""}
                                    </span>
                                )}
                                <button
                                    onClick={() => handleCheck(em.id)}
                                    disabled={checking === em.id}
                                    className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50"
                                >
                                    {checking === em.id ? "Checking…" : "Run Check"}
                                </button>
                                <button
                                    onClick={() => handleRemove(em.id)}
                                    className="text-xs text-red-400 hover:text-red-300 transition-colors"
                                >
                                    Remove
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
