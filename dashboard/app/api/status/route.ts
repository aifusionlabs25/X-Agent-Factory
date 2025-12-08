import { NextResponse } from 'next/server';

export async function GET() {
    const status = {
        timestamp: new Date().toISOString(),
        services: {
            ollama: { status: 'unknown', latency: 0, model: null as string | null },
            gemini: { status: 'unknown', latency: 0, tokens_used_today: 0 },
            tavus: { status: 'unknown', latency: 0, minutes_used: 0, minutes_remaining: 0, replicas_count: 0 },
            elevenlabs: { status: 'unknown', latency: 0, characters_used: 0, characters_limit: 0, voice: null as string | null }
        }
    };

    // ============================================================
    // 1. OLLAMA (Local) - Check if running
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
    // 2. GEMINI - Check API health (no usage API available)
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
            // Note: Google doesn't expose usage via API - would need Cloud Console billing API
        } catch (e) {
            status.services.gemini.status = 'offline';
        }
    } else {
        status.services.gemini.status = 'no_key';
    }

    // ============================================================
    // 3. TAVUS - Get replicas count (no billing API exposed)
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
                // Note: Tavus doesn't expose billing/usage via API
                // These would need to be tracked locally or via Tavus dashboard scraping
                status.services.tavus.minutes_used = 0; // Placeholder
                status.services.tavus.minutes_remaining = 1000; // Placeholder
            } else {
                status.services.tavus.status = 'error';
            }
        } catch (e: any) {
            status.services.tavus.status = 'timeout';
            console.error('Tavus error:', e.message);
        }
    } else {
        status.services.tavus.status = 'no_key';
    }

    // ============================================================
    // 4. ELEVENLABS - Get real subscription data
    // ============================================================
    const elevenLabsKey = process.env.ELEVENLABS_API_KEY;
    if (elevenLabsKey) {
        try {
            const start = Date.now();

            // Get user subscription info
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
                // Fallback to /v1/user if subscription fails
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

            // Get voices to show active voice
            const voicesRes = await fetch('https://api.elevenlabs.io/v1/voices', {
                headers: { 'xi-api-key': elevenLabsKey },
                signal: AbortSignal.timeout(5000)
            });

            if (voicesRes.ok) {
                const voicesData = await voicesRes.json();
                // Get first custom voice or first available
                const customVoice = voicesData.voices?.find((v: any) => v.category === 'cloned');
                const firstVoice = voicesData.voices?.[0];
                status.services.elevenlabs.voice = customVoice?.name || firstVoice?.name || 'Default';
            }

        } catch (e: any) {
            status.services.elevenlabs.status = 'offline';
            console.error('ElevenLabs error:', e.message);
        }
    } else {
        status.services.elevenlabs.status = 'no_key';
    }

    return NextResponse.json(status);
}
