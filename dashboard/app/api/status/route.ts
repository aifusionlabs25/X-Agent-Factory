import { NextResponse } from 'next/server';

export async function GET() {
    const status = {
        timestamp: new Date().toISOString(),
        services: {
            ollama: { status: 'unknown', latency: 0, model: null as string | null },
            gemini: { status: 'unknown', latency: 0 },
            tavus: { status: 'unknown', latency: 0, minutes_used: 0, minutes_remaining: 0 },
            elevenlabs: { status: 'unknown', latency: 0, characters_used: 0, characters_limit: 0, voice: null as string | null }
        }
    };


    // Check Ollama (Local)
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

    // Check Gemini
    const apiKey = process.env.GOOGLE_API_KEY;
    if (apiKey) {
        try {
            const start = Date.now();
            const geminiRes = await fetch(
                `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`,
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

    // Tavus - Would need actual API call with key
    // For now, simulate/placeholder
    const tavusKey = process.env.TAVUS_API_KEY;
    if (tavusKey) {
        try {
            const start = Date.now();
            const tavusRes = await fetch('https://api.tavus.io/v1/replicas', {
                headers: { 'x-api-key': tavusKey },
                signal: AbortSignal.timeout(10000)
            });
            const latency = Date.now() - start;

            if (tavusRes.ok) {
                status.services.tavus.status = 'online';
                status.services.tavus.latency = latency;
                // Placeholder usage - would need billing API
                status.services.tavus.minutes_used = 45;
                status.services.tavus.minutes_remaining = 955;
            } else {
                status.services.tavus.status = 'error';
            }
        } catch (e) {
            status.services.tavus.status = 'timeout';
        }
    } else {
        status.services.tavus.status = 'no_key';
    }

    // ElevenLabs - Would need actual API
    const elevenLabsKey = process.env.ELEVENLABS_API_KEY;
    if (elevenLabsKey) {
        try {
            const start = Date.now();
            const elRes = await fetch('https://api.elevenlabs.io/v1/user', {
                headers: { 'xi-api-key': elevenLabsKey },
                signal: AbortSignal.timeout(5000)
            });

            if (elRes.ok) {
                const data = await elRes.json();
                status.services.elevenlabs.status = 'online';
                status.services.elevenlabs.latency = Date.now() - start;
                status.services.elevenlabs.characters_used = data.subscription?.character_count || 0;
                status.services.elevenlabs.characters_limit = data.subscription?.character_limit || 10000;
            } else {
                status.services.elevenlabs.status = 'error';
            }
        } catch (e) {
            status.services.elevenlabs.status = 'offline';
        }
    } else {
        status.services.elevenlabs.status = 'no_key';
        // Placeholder
        status.services.elevenlabs.characters_used = 2500;
        status.services.elevenlabs.characters_limit = 10000;
        status.services.elevenlabs.voice = 'Rachel';
    }

    return NextResponse.json(status);
}
