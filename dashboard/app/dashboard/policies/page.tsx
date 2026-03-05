"use client";

import { useState } from "react";
import { fetchPolicies, fetchTools, upsertPolicy, deletePolicy, getRole } from "@/lib/api";
import { useApi } from "@/lib/hooks";

export default function PoliciesPage() {
    const { data: policies, refetch } = useApi<any[]>(fetchPolicies);
    const { data: tools } = useApi<any[]>(fetchTools);
    const role = getRole();
    const isAdmin = role === "admin";

    // New policy form
    const [selectedTool, setSelectedTool] = useState<number>(0);
    const [selectedAction, setSelectedAction] = useState("warn");
    const [selectedAlt, setSelectedAlt] = useState<number | null>(null);
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        if (!selectedTool) return;
        setSaving(true);
        try {
            await upsertPolicy({ tool_id: selectedTool, action: selectedAction, alternative_tool_id: selectedAlt });
            refetch();
            setSelectedTool(0);
        } catch (e) {
            alert("Failed to save policy");
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Remove this policy rule?")) return;
        await deletePolicy(id);
        refetch();
    };

    const actionColors: Record<string, string> = {
        allow: "bg-emerald-900/30 text-emerald-400 border-emerald-800/30",
        warn: "bg-amber-900/30 text-amber-400 border-amber-800/30",
        block: "bg-red-900/30 text-red-400 border-red-800/30",
    };

    return (
        <div className="space-y-8 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Policies</h2>
                <p className="text-slate-400 text-sm mt-1">Configure allow / warn / block rules for AI tools</p>
            </div>

            {/* Add / Edit policy */}
            {isAdmin && (
                <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-slate-300 mb-4">Add / Update Policy Rule</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
                        <div>
                            <label className="text-xs text-slate-500 mb-1 block">AI Tool</label>
                            <select
                                value={selectedTool}
                                onChange={(e) => setSelectedTool(Number(e.target.value))}
                                className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-sm text-slate-200 outline-none focus:border-indigo-500"
                            >
                                <option value={0}>Select tool…</option>
                                {tools?.map((t) => (
                                    <option key={t.id} value={t.id}>{t.name} ({t.domain})</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 mb-1 block">Action</label>
                            <select
                                value={selectedAction}
                                onChange={(e) => setSelectedAction(e.target.value)}
                                className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-sm text-slate-200 outline-none focus:border-indigo-500"
                            >
                                <option value="allow">Allow</option>
                                <option value="warn">Warn</option>
                                <option value="block">Block</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 mb-1 block">Approved Alt (optional)</label>
                            <select
                                value={selectedAlt ?? ""}
                                onChange={(e) => setSelectedAlt(e.target.value ? Number(e.target.value) : null)}
                                className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-sm text-slate-200 outline-none focus:border-indigo-500"
                            >
                                <option value="">None</option>
                                {tools?.map((t) => (
                                    <option key={t.id} value={t.id}>{t.name}</option>
                                ))}
                            </select>
                        </div>
                        <button
                            onClick={handleSave}
                            disabled={saving || !selectedTool}
                            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition disabled:opacity-40"
                        >
                            {saving ? "Saving…" : "Save"}
                        </button>
                    </div>
                </div>
            )}

            {/* Current policies table */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-[#334155]">
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Tool</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Domain</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Action</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Alternative</th>
                            {isAdmin && <th className="w-16" />}
                        </tr>
                    </thead>
                    <tbody>
                        {policies && policies.length > 0 ? policies.map((p: any) => (
                            <tr key={p.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/30 transition-colors">
                                <td className="px-5 py-3 text-slate-200">{p.tool_name}</td>
                                <td className="px-5 py-3 font-mono text-xs text-slate-400">{p.tool_domain}</td>
                                <td className="px-5 py-3">
                                    <span className={`text-xs px-2.5 py-1 rounded-full border capitalize ${actionColors[p.action] || "text-slate-400"}`}>
                                        {p.action}
                                    </span>
                                </td>
                                <td className="px-5 py-3 text-slate-400 text-xs">{p.alternative_name || "—"}</td>
                                {isAdmin && (
                                    <td className="px-3 py-3">
                                        <button onClick={() => handleDelete(p.id)} className="text-red-500 hover:text-red-400 text-xs">✕</button>
                                    </td>
                                )}
                            </tr>
                        )) : (
                            <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-500">No policies configured yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
