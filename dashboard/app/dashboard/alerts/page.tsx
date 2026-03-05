"use client";

import { fetchAlerts } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { AlertTriangle, TrendingUp, AlertCircle } from "lucide-react";

export default function AlertsPage() {
    const { data: alerts, loading } = useApi<any[]>(fetchAlerts);

    const getSeverityBadge = (severity: string) => {
        switch (severity.toLowerCase()) {
            case "high":
                return <span className="text-xs px-2.5 py-1 rounded-full border bg-red-900/30 text-red-400 border-red-800/30">High</span>;
            case "medium":
            case "med":
                return <span className="text-xs px-2.5 py-1 rounded-full border bg-amber-900/30 text-amber-400 border-amber-800/30">Medium</span>;
            default:
                return <span className="text-xs px-2.5 py-1 rounded-full border bg-slate-800 text-slate-400 border-slate-700">Low</span>;
        }
    };

    const getAlertIcon = (type: string) => {
        if (type === "SpikeUsage") return <TrendingUp className="w-5 h-5 text-amber-400" />;
        if (type === "HighRiskToolAccess") return <AlertTriangle className="w-5 h-5 text-red-400" />;
        return <AlertCircle className="w-5 h-5 text-indigo-400" />;
    };

    return (
        <div className="space-y-6 max-w-5xl">
            <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <AlertTriangle className="w-6 h-6 text-red-500" /> Security Alerts
                </h2>
                <p className="text-slate-400 text-sm mt-1">Automated SOC alerts for anomalous AI usage</p>
            </div>

            <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-[#334155]">
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium w-12"></th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Timestamp</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Type</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Domain</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Severity</th>
                            <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium">Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && (
                            <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-500">Loading alerts…</td></tr>
                        )}
                        {alerts && alerts.length > 0 ? alerts.map((a: any) => (
                            <tr key={a.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/30 transition-colors">
                                <td className="px-5 py-4">{getAlertIcon(a.alert_type)}</td>
                                <td className="px-5 py-4 text-slate-400 text-xs font-mono whitespace-nowrap">
                                    {new Date(a.timestamp).toLocaleString()}
                                </td>
                                <td className="px-5 py-4 text-slate-200 font-medium">
                                    {a.alert_type.replace(/([A-Z])/g, ' $1').trim()}
                                </td>
                                <td className="px-5 py-4 text-slate-300 font-mono text-xs">{a.domain}</td>
                                <td className="px-5 py-4">{getSeverityBadge(a.severity)}</td>
                                <td className="px-5 py-4 text-slate-400 text-xs">
                                    {a.alert_type === "SpikeUsage" ? `Hit threshold: ${a.count_threshold} events` : 'Access blocked/warned for critical risk domain'}
                                </td>
                            </tr>
                        )) : (
                            !loading && <tr><td colSpan={6} className="px-5 py-12 text-center text-slate-500">No active security alerts. You are safe!</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
