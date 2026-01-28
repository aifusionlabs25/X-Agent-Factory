import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Helper to update .env.local safely
function updateEnvLocal(newSecrets: Record<string, string>) {
    const envPath = path.join(process.cwd(), '.env.local');
    let envContent = '';

    if (fs.existsSync(envPath)) {
        envContent = fs.readFileSync(envPath, 'utf-8');
    }

    const existingLines = envContent.split('\n');
    const existingKeys = new Set();

    // Update map for O(1) tracking
    const updatedLines = existingLines.map(line => {
        const match = line.match(/^([^=]+)=/);
        if (match) {
            const key = match[1].trim();
            existingKeys.add(key);
            if (newSecrets[key] && newSecrets[key].length > 0) {
                // Replace existing secret
                return `${key}=${newSecrets[key]}`;
            }
        }
        return line;
    });

    // Append new secrets
    for (const [key, val] of Object.entries(newSecrets)) {
        if (!existingKeys.has(key) && val.length > 0) {
            updatedLines.push(`${key}=${val}`);
        }
    }

    // Write back
    fs.writeFileSync(envPath, updatedLines.join('\n').replace(/\n{2,}/g, '\n').trim() + '\n');
}

export async function GET(request: Request, { params }: { params: { client: string } }) {
    const { client } = params;
    const baseDir = path.join(process.cwd(), '..', 'agents', 'clients', client);
    const profilePath = path.join(baseDir, 'runtime_profile.json');

    if (!fs.existsSync(profilePath)) {
        return NextResponse.json({
            exists: false,
            profile: null,
            secretStatus: { tavus: false, cartesia: false }
        });
    }

    try {
        const rawData = fs.readFileSync(profilePath, 'utf8');
        const profile = JSON.parse(rawData);

        // Check secrets status (DO NOT RETURN ACTUAL SECRETS)
        // We check process.env which should be loaded by Next.js
        const secretStatus = {
            tavus: false,
            tts: false
        };

        // Check Tavus Secret (Dynamic Ref)
        const tavusRef = profile.providers?.tavus?.api_key_ref;
        if (tavusRef?.startsWith("ENV:")) {
            const key = tavusRef.split(":")[1];
            if (process.env[key]) secretStatus.tavus = true;
        }

        // Check TTS Secret (Dynamic Ref)
        const ttsRef = profile.providers?.tts?.api_key_ref;
        if (ttsRef?.startsWith("ENV:")) {
            const key = ttsRef.split(":")[1];
            if (process.env[key]) secretStatus.tts = true;
        }

        return NextResponse.json({
            exists: true,
            profile,
            secretStatus
        });

    } catch (error) {
        return NextResponse.json({ error: 'Failed to read runtime profile' }, { status: 500 });
    }
}

export async function POST(request: Request, { params }: { params: { client: string } }) {
    const { client } = params;
    try {
        const body = await request.json();
        const { profile, secretsToSave } = body;

        const baseDir = path.join(process.cwd(), '..', 'agents', 'clients', client);
        const profilePath = path.join(baseDir, 'runtime_profile.json');

        // 1. Save Profile
        if (profile) {
            // Ensure directory exists (it should)
            if (!fs.existsSync(baseDir)) {
                return NextResponse.json({ error: 'Agent directory missing' }, { status: 404 });
            }
            fs.writeFileSync(profilePath, JSON.stringify(profile, null, 2));
        }

        // 2. Save Secrets (if any)
        let secretUpdateStatus = "No secrets updated";
        if (secretsToSave && Object.keys(secretsToSave).length > 0) {
            updateEnvLocal(secretsToSave);
            secretUpdateStatus = "Secrets written to .env.local";
        }

        return NextResponse.json({ success: true, secretUpdateStatus });

    } catch (error) {
        console.error("Runtime Save Error:", error);
        return NextResponse.json({ error: 'Failed to save runtime profile' }, { status: 500 });
    }
}
