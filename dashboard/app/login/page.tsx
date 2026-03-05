"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";

export default function LoginPage() {
    const router = useRouter();
    const [isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [orgName, setOrgName] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            if (isRegister) {
                await register(email, password, orgName);
            } else {
                await login(email, password);
            }
            router.push("/dashboard");
        } catch (err: any) {
            setError(err.message || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#0f172a] px-4">
            <div className="w-full max-w-md">
                {/* Logo / Header */}
                <div className="text-center mb-8">
                    <div className="text-5xl mb-4">🛡️</div>
                    <h1 className="text-2xl font-bold text-white">Shadow AI Detector</h1>
                    <p className="text-slate-400 text-sm mt-2">
                        Privacy-first AI usage monitoring
                    </p>
                </div>

                {/* Card */}
                <div className="bg-[#1e293b] border border-[#334155] rounded-2xl p-8 shadow-2xl shadow-indigo-900/10">
                    <h2 className="text-lg font-semibold text-white mb-6">
                        {isRegister ? "Create an account" : "Sign in to dashboard"}
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {isRegister && (
                            <div>
                                <label className="block text-xs text-slate-400 mb-1.5">Organization Name</label>
                                <input
                                    type="text"
                                    value={orgName}
                                    onChange={(e) => setOrgName(e.target.value)}
                                    required={isRegister}
                                    className="w-full px-3 py-2.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm placeholder:text-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition"
                                    placeholder="Acme Corp"
                                />
                            </div>
                        )}
                        <div>
                            <label className="block text-xs text-slate-400 mb-1.5">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full px-3 py-2.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm placeholder:text-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition"
                                placeholder="admin@company.com"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1.5">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="w-full px-3 py-2.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm placeholder:text-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition"
                                placeholder="••••••••"
                            />
                        </div>

                        {error && (
                            <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/30 rounded-lg px-3 py-2">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors disabled:opacity-50"
                        >
                            {loading ? "Please wait…" : isRegister ? "Register" : "Sign In"}
                        </button>
                    </form>

                    <div className="mt-5 text-center">
                        <button
                            onClick={() => { setIsRegister(!isRegister); setError(""); }}
                            className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                        >
                            {isRegister ? "Already have an account? Sign in" : "Need an account? Register"}
                        </button>
                    </div>
                </div>

                <p className="text-center text-xs text-slate-600 mt-6">
                    Domain-level monitoring only · No content captured
                </p>
            </div>
        </div>
    );
}
