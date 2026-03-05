"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register, personalLogin, personalRegister } from "@/lib/api";

export default function LoginPage() {
    const router = useRouter();
    const [authType, setAuthType] = useState<"org" | "personal">("org");
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
            if (authType === "org") {
                if (isRegister) {
                    await register(email, password, orgName);
                } else {
                    await login(email, password);
                }
                router.push("/dashboard");
            } else {
                if (isRegister) {
                    await personalRegister(email, password);
                } else {
                    await personalLogin(email, password);
                }
                router.push("/personal");
            }
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
                    <h1 className="text-2xl font-bold text-white">ShieldOps</h1>
                    <p className="text-slate-400 text-sm mt-2">
                        Shadow AI Detector · Breach Monitor
                    </p>
                </div>

                {/* Module Tabs */}
                <div className="flex mb-4 bg-[#1e293b] rounded-xl p-1 border border-[#334155]">
                    <button
                        onClick={() => { setAuthType("org"); setIsRegister(false); setError(""); }}
                        className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${authType === "org"
                                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-900/30"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                    >
                        🏢 Organization
                    </button>
                    <button
                        onClick={() => { setAuthType("personal"); setIsRegister(false); setError(""); }}
                        className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${authType === "personal"
                                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/30"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                    >
                        👤 Personal
                    </button>
                </div>

                {/* Card */}
                <div className="bg-[#1e293b] border border-[#334155] rounded-2xl p-8 shadow-2xl shadow-indigo-900/10">
                    <h2 className="text-lg font-semibold text-white mb-1">
                        {isRegister ? "Create an account" : "Sign in"}
                    </h2>
                    <p className="text-xs text-slate-500 mb-6">
                        {authType === "org"
                            ? "Shadow AI Detector — Org admin dashboard"
                            : "Breach Monitor — Personal security tools"
                        }
                    </p>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {isRegister && authType === "org" && (
                            <div>
                                <label className="block text-xs text-slate-400 mb-1.5">Organization Name</label>
                                <input
                                    type="text"
                                    value={orgName}
                                    onChange={(e) => setOrgName(e.target.value)}
                                    required
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
                                placeholder={authType === "org" ? "admin@company.com" : "you@gmail.com"}
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
                            className={`w-full py-2.5 rounded-lg font-semibold text-sm transition-all disabled:opacity-50 ${authType === "org"
                                    ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                                    : "bg-emerald-600 hover:bg-emerald-500 text-white"
                                }`}
                        >
                            {loading ? "Please wait…" : isRegister ? "Create Account" : "Sign In"}
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
                    {authType === "org"
                        ? "Domain-level monitoring only · No content captured"
                        : "No passwords stored · Privacy-first breach monitoring"
                    }
                </p>
            </div>
        </div>
    );
}
