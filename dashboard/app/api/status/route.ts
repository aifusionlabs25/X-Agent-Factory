import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

interface GeminiLog {
    timestamp: string;
    model: string;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    success: boolean;
}

interface TavusLog {
    timestamp: string;
    replica_id: string;
    client_slug: string;
    conversation_id: string | null;
    status: string;
    duration_seconds: number | null;
}

function getGeminiUsage() {
    const cwd = path.join(process.cwd(), '..');
    const logPath = path.join(cwd, 'intelligence', 'usage', 'gemini_log.json');

    if (!fs.existsSync(logPath)) {
        return {
            total_calls: 0,
            total_input_tokens: 0,
            total_output_tokens: 0,
            total_tokens: 0,
            estimated_cost_usd: 0,
            successful_calls: 0,
            failed_calls: 0
        };
    }

    const logs: GeminiLog[] = JSON.parse(fs.readFileSync(logPath, 'utf-8'));

    const totalInput = logs.reduce((sum, e) => sum + (e.input_tokens || 0), 0);
    const totalOutput = logs.reduce((sum, e) => sum + (e.output_tokens || 0), 0);
    const successful = logs.filter(e => e.success !== false).length;

    // Gemini Flash pricing: ~$0.35 per 1M input, ~$1.05 per 1M output
    const cost = (totalInput * 0.35 / 1_000_000) + (totalOutput * 1.05 / 1_000_000);

    return {
        total_calls: logs.length,
        total_input_tokens: totalInput,
        total_output_tokens: totalOutput,
        total_tokens: totalInput + totalOutput,
        estimated_cost_usd: Math.round(cost * 10000) / 10000,
        successful_calls: successful,
        failed_calls: logs.length - successful
    };
}

function getTavusUsage() {
    const cwd = path.join(process.cwd(), '..');
    const logPath = path.join(cwd, 'intelligence', 'usage', 'tavus_log.json');

    if (!fs.existsSync(logPath)) {
        return {
            total_calls: 0,
            total_minutes: 0,
            total_seconds: 0,
            completed_calls: 0,
            active_calls: 0
        };
    }

    const logs: TavusLog[] = JSON.parse(fs.readFileSync(logPath, 'utf-8'));

    const completed = logs.filter(e => e.status === 'ended');
    const active = logs.filter(e => e.status === 'started');

    // Sum durations, rounding each call up to minimum 1 minute
    const totalSeconds = completed.reduce((sum, e) => sum + (e.duration_seconds || 0), 0);
    const totalMinutes = completed.reduce((sum, e) => {
        const secs = e.duration_seconds || 60;
        return sum + Math.max(1, Math.ceil(secs / 60));
    }, 0);

    return {
        total_calls: logs.length,
        total_minutes: totalMinutes,
        total_seconds: totalSeconds,
        completed_calls: completed.length,
        active_calls: active.length
    };
}

export async function GET() {
    const status = {
        timestamp: new Date().toISOString(),
        services: {
            ollama: { status: 'unknown', latency: 0, model: null as string | null },
            gemini: { status: 'unknown', latency: 0, usage: null as any },
            tavus: { status: 'unknown', latency: 0, replicas_count: 0, usage: null as any },
            elevenlabs: { status: 'unknown', latency: 0, characters_used: 0, characters_limit: 0, voice: null as string | null }
        }
    };

    // ============================================================
    // 1. OLLAMA (Local)
    // ============================================================
    try {
        const start = Date.now();
        const ollamaRes = await fetch('http://localhost:11434/api/tags', {
            signal: AbortSignal.timeout(5000)
        });
        status.services.ollama.latency = Date.now() - start;

        if (ollamaRes.ok) {
            const data = await ollamaRes.json();
            status.services.ollama.status = 'online';
            status.services.ollama.model = data.models?.[0]?.name || 'No model loaded';
        } else {
            status.services.ollama.status = 'error';
        }
    } catch (e) {
        status.services.ollama.status = 'offline';
    }

    // ============================================================
    // 2. GEMINI - Check API health + local usage tracking
    // ============================================================
    const googleApiKey = process.env.GOOGLE_API_KEY;
    if (googleApiKey) {
        try {
            const start = Date.now();
            const geminiRes = await fetch(
                `https://generativelanguage.googleapis.com/v1beta/models?key=${googleApiKey}`,
                { signal: AbortSignal.timeout(5000) }
            );
            status.services.gemini.latency = Date.now() - start;
            status.services.gemini.status = geminiRes.ok ? 'online' : 'error';
        } catch (e) {
            status.services.gemini.status = 'offline';
        }
    } else {
        status.services.gemini.status = 'no_key';
    }

    // Add local usage data
    status.services.gemini.usage = getGeminiUsage();

    // ============================================================
    // 3. TAVUS - Check API + local usage tracking
    // ============================================================
    const tavusKey = process.env.TAVUS_API_KEY;
    if (tavusKey) {
        try {
            const start = Date.now();
            const tavusRes = await fetch('https://api.tavus.io/v2/replicas', {
                headers: { 'x-api-key': tavusKey },
                signal: AbortSignal.timeout(10000)
            });
            status.services.tavus.latency = Date.now() - start;

            if (tavusRes.ok) {
                const data = await tavusRes.json();
                status.services.tavus.status = 'online';
                status.services.tavus.replicas_count = data.data?.length || 0;
            } else {
                status.services.tavus.status = 'error';
            }
        } catch (e: any) {
            status.services.tavus.status = 'timeout';
        }
    } else {
        status.services.tavus.status = 'no_key';
    }

    // Add local usage data
    status.services.tavus.usage = getTavusUsage();

    // ============================================================
    // 4. ELEVENLABS - Real subscription data
    // ============================================================
    const elevenLabsKey = process.env.ELEVENLABS_API_KEY;
    if (elevenLabsKey) {
        try {
            const start = Date.now();
            const userRes = await fetch('https://api.elevenlabs.io/v1/user/subscription', {
                headers: { 'xi-api-key': elevenLabsKey },
                signal: AbortSignal.timeout(5000)
            });

            if (userRes.ok) {
                const userData = await userRes.json();
                status.services.elevenlabs.status = 'online';
                status.services.elevenlabs.latency = Date.now() - start;
                status.services.elevenlabs.characters_used = userData.character_count || 0;
                status.services.elevenlabs.characters_limit = userData.character_limit || 10000;
            } else {
                const fallbackRes = await fetch('https://api.elevenlabs.io/v1/user', {
                    headers: { 'xi-api-key': elevenLabsKey },
                    signal: AbortSignal.timeout(5000)
                });

                if (fallbackRes.ok) {
                    const fallbackData = await fallbackRes.json();
                    status.services.elevenlabs.status = 'online';
                    status.services.elevenlabs.latency = Date.now() - start;
                    status.services.elevenlabs.characters_used = fallbackData.subscription?.character_count || 0;
                    status.services.elevenlabs.characters_limit = fallbackData.subscription?.character_limit || 10000;
                } else {
                    status.services.elevenlabs.status = 'error';
                }
            }

            const voicesRes = await fetch('https://api.elevenlabs.io/v1/voices', {
                headers: { 'xi-api-key': elevenLabsKey },
                signal: AbortSignal.timeout(5000)
            });

            if (voicesRes.ok) {
                const voicesData = await voicesRes.json();
                const customVoice = voicesData.voices?.find((v: any) => v.category === 'cloned');
                const firstVoice = voicesData.voices?.[0];
                status.services.elevenlabs.voice = customVoice?.name || firstVoice?.name || 'Default';
            }

        } catch (e: any) {
            status.services.elevenlabs.status = 'offline';
        }
    } else {
        status.services.elevenlabs.status = 'no_key';
    }

    return NextResponse.json(status);
}
