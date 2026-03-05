"use client";

import { fetchAuditLogs } from "@/lib/api";
import { useApi } from "@/lib/hooks";

export default function AuditPage() {
    const { data: logs, loading } = useApi<any[]>(fetchAuditLogs);

    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold text-white">Audit Logs</h2>
                <p className="text-slate-400 text-sm mt-1">History of administrative actions</p>
            </div>

            <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-[#334155]">
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Timestamp</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Admin</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Action</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Detail</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && (
                            <tr><td colSpan={4} className="px-5 py-8 text-center text-slate-500">Loading…</td></tr>
                        )}
                        {logs && logs.length > 0 ? logs.map((l: any) => {
                            let detailView = <span className="text-slate-500">—</span>;

                            if (l.detail) {
                                try {
                                    const parsed = JSON.parse(l.detail);
                                    if (parsed.before || parsed.after) {
                                        detailView = (
                                            <div className="flex flex-col gap-1">
                                                {parsed.before && <span className="text-red-400">Before: {parsed.before.action} (Alt: {parsed.before.alternative_tool_id || 'none'})</span>}
                                                {parsed.after && <span className="text-emerald-400">After: {parsed.after.action} (Alt: {parsed.after.alternative_tool_id || 'none'})</span>}
                                            </div>
                                        );
                                    } else {
                                        detailView = <span>{l.detail}</span>;
                                    }
                                } catch (_) {
                                    detailView = <span>{l.detail}</span>;
                                }
                            }

                            return (
                                <tr key={l.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/30 transition-colors">
                                    <td className="px-5 py-3 text-slate-400 text-xs font-mono whitespace-nowrap">
                                        <div className="flex flex-col">
                                            <span>{new Date(l.timestamp).toLocaleString()}</span>
                                            {l.ip_address && <span className="text-[10px] text-slate-500 mt-1" title={l.user_agent}>IP: {l.ip_address}</span>}
                                        </div>
                                    </td>
                                    <td className="px-5 py-3 text-slate-300">{l.admin_email}</td>
                                    <td className="px-5 py-3">
                                        <span className={`text-xs px-2.5 py-1 rounded-full border bg-indigo-900/30 text-indigo-400 border-indigo-800/30 capitalize`}>
                                            {l.action.replace(/_/g, " ")}
                                        </span>
                                    </td>
                                    <td className="px-5 py-3 text-slate-400 text-xs">{detailView}</td>
                                </tr>
                            );
                        }) : (
                            !loading && <tr><td colSpan={4} className="px-5 py-8 text-center text-slate-500">No audit logs yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
