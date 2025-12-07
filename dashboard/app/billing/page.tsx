import React from 'react';

export default function BillingPage() {
    return (
        <div className="p-8">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-slate-800 tracking-tight">💳 BILLING & SUBSCRIPTIONS</h1>
                <p className="text-slate-500 font-mono">manage revenue streams</p>
            </header>

            <div className="grid grid-cols-3 gap-8">
                {/* Tier 1 */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm opacity-50">
                    <h3 className="text-xl font-bold text-slate-800">Standard</h3>
                    <p className="text-3xl font-black text-slate-900 mt-2">$150<span className="text-sm font-normal text-slate-500">/mo</span></p>
                    <ul className="mt-4 space-y-2 text-sm text-slate-600">
                        <li>✅ Triage Agent</li>
                        <li>✅ 500 Calls/mo</li>
                    </ul>
                </div>

                {/* Tier 2 (Active) */}
                <div className="bg-white p-6 rounded-xl border-2 border-green-500 shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-green-500 text-white text-xs px-2 py-1 font-bold">RECOMENDED</div>
                    <h3 className="text-xl font-bold text-slate-800">Professional</h3>
                    <p className="text-3xl font-black text-slate-900 mt-2">$299<span className="text-sm font-normal text-slate-500">/mo</span></p>
                    <ul className="mt-4 space-y-2 text-sm text-slate-600">
                        <li>✅ Triage + Scheduling</li>
                        <li>✅ Unlimited Calls</li>
                        <li>✅ Custom Voice Clone</li>
                    </ul>
                    <button className="w-full mt-6 bg-green-600 text-white font-bold py-2 rounded hover:bg-green-700">
                        Connect Stripe
                    </button>
                </div>

                {/* Tier 3 */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm opacity-50">
                    <h3 className="text-xl font-bold text-slate-800">Enterprise</h3>
                    <p className="text-3xl font-black text-slate-900 mt-2">Custom</p>
                    <ul className="mt-4 space-y-2 text-sm text-slate-600">
                        <li>✅ White Label</li>
                        <li>✅ API Access</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
