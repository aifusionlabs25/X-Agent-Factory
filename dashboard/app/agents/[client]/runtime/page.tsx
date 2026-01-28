'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { VOICE_PRESETS, VoicePreset } from '@/app/data/voice_presets';

export default function RuntimeConfigPage() {
    const params = useParams();
    const router = useRouter();
    const clientSlug = params.client as string;

    const [loading, setLoading] = useState(true);
    const [profile, setProfile] = useState<any>({
        agent_slug: clientSlug,
        // defaults
        runtime: { environment: 'local', primary_channel: 'voice' },
        providers: {
            tavus: { enabled: true, llm_provider: 'openai' },
            tts: { enabled: false, engine: 'cartesia' }
        },
        secrets: {}
    });

    const [secretStatus, setSecretStatus] = useState<any>({});
    const [secretsInput, setSecretsInput] = useState<any>({});
    const [verifyResult, setVerifyResult] = useState<string | null>(null);
    const [missingFields, setMissingFields] = useState<string[]>([]);

    useEffect(() => {
        fetchProfile();
    }, [clientSlug]);

    async function fetchProfile() {
        try {
            const res = await fetch(`/api/agent/${clientSlug}/runtime`);
            const data = await res.json();
            if (data.exists && data.profile) {
                setProfile(data.profile);
            }
            if (data.secretStatus) {
                setSecretStatus(data.secretStatus);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    // --- LOGIC ---
    function getSecretKeyName(provider: 'tavus' | 'tts') {
        const suffix = clientSlug.toUpperCase().replace(/-/g, '_');
        if (provider === 'tavus') return `TAVUS_API_KEY__${suffix}`;
        if (provider === 'tts') return `CARTESIA_API_KEY__${suffix}`; // Default to Cartesia for now
        return '';
    }

    function applyPreset(presetId: string) {
        const preset = VOICE_PRESETS.find(p => p.id === presetId);
        if (!preset) return;

        const newTTS = {
            ...profile.providers.tts,
            voice_settings_preset: preset.id,
            voice_settings_json: preset.settings,
            engine: preset.engine
        };
        setProfile({
            ...profile,
            providers: { ...profile.providers, tts: newTTS }
        });
    }

    function validate() {
        const missing = [];

        // Tavus Checks
        if (profile.providers?.tavus?.enabled) {
            if (!profile.providers.tavus.persona_id) missing.push("Tavus Persona ID");
            if (!profile.providers.tavus.replica_id) missing.push("Tavus Replica ID");
            if (!profile.providers.tavus.key_name) missing.push("Tavus Key Name");
            if (!secretStatus.tavus && !secretsInput[getSecretKeyName('tavus')]) missing.push("Tavus API Key (Env)");
        }

        // TTS Checks
        if (profile.providers?.tts?.enabled) {
            if (!profile.providers.tts.external_voice_id) missing.push("TTS Voice ID");
            if (!profile.providers.tts.voice_settings_preset) missing.push("Voice Preset");
            if (!secretStatus.tts && !secretsInput[getSecretKeyName('tts')]) missing.push("TTS API Key (Env)");
        }

        setMissingFields(missing);
        return missing.length === 0;
    }

    async function handleSave() {
        // We allow saving WIP, but we warn
        validate();

        // Construct dynamic refs
        const updatedProfile = { ...profile };
        // Tavus Secret Ref
        updatedProfile.providers.tavus.api_key_ref = `ENV:${getSecretKeyName('tavus')}`;
        // TTS Secret Ref
        updatedProfile.providers.tts.api_key_ref = `ENV:${getSecretKeyName('tts')}`;

        try {
            const payload = {
                profile: updatedProfile,
                secretsToSave: secretsInput
            };

            const res = await fetch(`/api/agent/${clientSlug}/runtime`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.success) {
                alert('Saved!');
                setSecretsInput({}); // Clear inputs
                fetchProfile(); // Refresh status
                validate(); // Re-validate to clear errors if resolved
            } else {
                alert('Error saving: ' + JSON.stringify(data));
            }
        } catch (e) {
            alert('Save failed');
        }
    }

    async function handleVerify() {
        if (!validate()) {
            alert("Cannot verify: Missing required fields.");
            return;
        }

        setVerifyResult('Running verification...');
        try {
            const res = await fetch(`/api/runtime/verify?client=${clientSlug}`);
            const data = await res.json();
            setVerifyResult(data.output);
        } catch (e) {
            setVerifyResult('Verification request failed.');
        }
    }

    if (loading) return <div className="p-8 text-neutral-400">Loading Runtime Config...</div>;

    const valid = missingFields.length === 0;

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-mono">
            <header className="mb-8 flex justify-between items-center border-b border-slate-800 pb-4">
                <div>
                    <h1 className="text-2xl font-bold text-emerald-400">Runtime Binding v2: {clientSlug}</h1>
                    <p className="text-slate-500 text-sm mt-1">Per-Agent Credentials & Voice Settings</p>
                </div>
                <div className="space-x-4">
                    <button onClick={() => router.push(`/agents/${clientSlug}`)} className="text-slate-400 hover:text-white">Back to Agent</button>
                    <button onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded font-bold transition-colors">
                        SAVE CONFIG
                    </button>
                </div>
            </header>

            {/* VALIDATION BANNER */}
            {!valid && (
                <div className="bg-red-900/30 border border-red-500 p-4 rounded mb-8">
                    <h3 className="text-red-400 font-bold mb-2">Configuration Incomplete</h3>
                    <ul className="list-disc list-inside text-sm text-red-200">
                        {missingFields.map(f => <li key={f}>Missing: {f}</li>)}
                    </ul>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* LEFT COLUMN: PROVIDERS */}
                <div className="space-y-8">

                    {/* TAVUS CONFIG */}
                    <section className={`border p-6 rounded-lg transition-colors ${profile.providers?.tavus?.enabled ? 'bg-slate-900 border-slate-700' : 'bg-slate-900/50 border-slate-800'}`}>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-white">1. Tavus (Video)</h2>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={profile.providers?.tavus?.enabled}
                                    onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tavus: { ...profile.providers.tavus, enabled: e.target.checked } } })}
                                />
                                <span className={profile.providers?.tavus?.enabled ? "text-emerald-400" : "text-slate-600"}>Enabled</span>
                            </label>
                        </div>

                        {profile.providers?.tavus?.enabled && (
                            <div className="space-y-4 border-l-2 border-slate-700 pl-4">
                                <div>
                                    <label className="block text-xs uppercase text-slate-500 mb-1">Key Name (Identifier)</label>
                                    <input
                                        className="w-full bg-slate-800 border border-slate-700 p-2 rounded text-sm text-white"
                                        value={profile.providers.tavus.key_name || ''}
                                        onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tavus: { ...profile.providers.tavus, key_name: e.target.value } } })}
                                        placeholder="e.g. James - Knowles Law Firm"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs uppercase text-slate-500 mb-1">Persona ID</label>
                                        <input
                                            className="w-full bg-slate-800 border border-slate-700 p-2 rounded text-sm text-white"
                                            value={profile.providers.tavus.persona_id || ''}
                                            onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tavus: { ...profile.providers.tavus, persona_id: e.target.value } } })}
                                            placeholder="p_123456"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs uppercase text-slate-500 mb-1">Replica ID</label>
                                        <input
                                            className="w-full bg-slate-800 border border-slate-700 p-2 rounded text-sm text-white"
                                            value={profile.providers.tavus.replica_id || ''}
                                            onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tavus: { ...profile.providers.tavus, replica_id: e.target.value } } })}
                                            placeholder="r_abcdef"
                                        />
                                    </div>
                                </div>

                                {/* PER AGENT SECRET INPUT */}
                                <div className="p-3 bg-slate-950 rounded border border-slate-800">
                                    <div className="flex justify-between mb-1">
                                        <label className="text-xs font-bold text-amber-500">API Key: {getSecretKeyName('tavus')}</label>
                                        <span className={secretStatus.tavus ? "text-emerald-500 text-[10px]" : "text-red-500 text-[10px]"}>
                                            {secretStatus.tavus ? "✅ PRESENT" : "❌ MISSING"}
                                        </span>
                                    </div>
                                    <input
                                        type="password"
                                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-sm text-white focus:border-amber-500 outline-none"
                                        placeholder={secretStatus.tavus ? "(Key Securely Stored)" : "Paste Agent-Specific Key..."}
                                        onChange={e => setSecretsInput({ ...secretsInput, [getSecretKeyName('tavus')]: e.target.value })}
                                    />
                                </div>
                            </div>
                        )}
                    </section>

                    {/* TTS CONFIG */}
                    <section className={`border p-6 rounded-lg transition-colors ${profile.providers?.tts?.enabled ? 'bg-slate-900 border-slate-700' : 'bg-slate-900/50 border-slate-800'}`}>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-white">2. TTS Engine (Voice)</h2>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={profile.providers?.tts?.enabled || false}
                                    onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tts: { ...profile.providers.tts, enabled: e.target.checked } } })}
                                />
                                <span className={profile.providers?.tts?.enabled ? "text-purple-400" : "text-slate-600"}>Enabled</span>
                            </label>
                        </div>
                        {profile.providers?.tts?.enabled && (
                            <div className="space-y-4 border-l-2 border-slate-700 pl-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs uppercase text-slate-500 mb-1">Engine</label>
                                        <select
                                            className="w-full bg-slate-800 border border-slate-700 p-2 rounded text-sm text-white"
                                            value={profile.providers.tts.engine || 'cartesia'}
                                            onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tts: { ...profile.providers.tts, engine: e.target.value } } })}
                                        >
                                            <option value="cartesia">Cartesia</option>
                                            <option value="elevenlabs">ElevenLabs</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs uppercase text-slate-500 mb-1">Voice Settings Preset</label>
                                        <select
                                            className="w-full bg-slate-800 border border-slate-700 p-2 rounded text-sm text-white"
                                            value={profile.providers.tts.voice_settings_preset || ''}
                                            onChange={e => applyPreset(e.target.value)}
                                        >
                                            <option value="">-- Select Preset --</option>
                                            {VOICE_PRESETS.map(p => (
                                                <option key={p.id} value={p.id}>{p.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs uppercase text-slate-500 mb-1">External Voice ID</label>
                                    <input
                                        className="w-full bg-slate-800 border border-slate-700 p-2 rounded text-sm text-white"
                                        value={profile.providers.tts.external_voice_id || ''}
                                        onChange={e => setProfile({ ...profile, providers: { ...profile.providers, tts: { ...profile.providers.tts, external_voice_id: e.target.value } } })}
                                        placeholder="e.g. 2489a8-...."
                                    />
                                </div>

                                {/* PER AGENT SECRET INPUT */}
                                <div className="p-3 bg-slate-950 rounded border border-slate-800">
                                    <div className="flex justify-between mb-1">
                                        <label className="text-xs font-bold text-amber-500">API Key: {getSecretKeyName('tts')}</label>
                                        <span className={secretStatus.tts ? "text-emerald-500 text-[10px]" : "text-red-500 text-[10px]"}>
                                            {secretStatus.tts ? "✅ PRESENT" : "❌ MISSING"}
                                        </span>
                                    </div>
                                    <input
                                        type="password"
                                        className="w-full bg-slate-900 border border-slate-700 p-2 rounded text-sm text-white focus:border-amber-500 outline-none"
                                        placeholder={secretStatus.tts ? "(Key Securely Stored)" : "Paste Agent-Specific Key..."}
                                        onChange={e => setSecretsInput({ ...secretsInput, [getSecretKeyName('tts')]: e.target.value })}
                                    />
                                </div>
                            </div>
                        )}
                    </section>

                </div>

                {/* RIGHT COLUMN: ACTIONS */}
                <div className="space-y-8">
                    {/* VERIFICATION */}
                    <section className="bg-slate-900 border border-slate-800 p-6 rounded-lg sticky top-8">
                        <h2 className="text-xl font-bold text-white mb-4">Verification Gate (G15.1)</h2>

                        {!valid ? (
                            <button
                                disabled
                                className="w-full bg-slate-700 text-slate-500 font-bold py-3 rounded mb-4 cursor-not-allowed"
                            >
                                FIX ISSUES TO VERIFY
                            </button>
                        ) : (
                            <button
                                onClick={handleVerify}
                                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded mb-4 shadow-lg shadow-indigo-900/50"
                            >
                                RUN VERIFICATION
                            </button>
                        )}

                        {verifyResult && (
                            <div className="bg-black p-4 rounded border border-slate-700 font-mono text-xs whitespace-pre-wrap overflow-x-auto text-slate-300">
                                {verifyResult}
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </div>
    );
}
