import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
    req: Request,
    { params }: { params: Promise<{ slug: string }> }
) {
    const { slug } = await params;

    if (!slug) {
        return NextResponse.json({ error: 'Client slug is required' }, { status: 400 });
    }

    // Construct paths to client data
    // Client data can be in either:
    // 1. /agents/{slug}/ (for pre-built agents like noah_home_services)
    // 2. /ingested_clients/{slug}/ (for spidered clients)
    const cwd = path.join(process.cwd(), '..');

    const agentPath = path.join(cwd, 'agents', slug);
    const ingestedPath = path.join(cwd, 'ingested_clients', slug);

    let clientDir: string | null = null;

    if (fs.existsSync(agentPath)) {
        clientDir = agentPath;
    } else if (fs.existsSync(ingestedPath)) {
        clientDir = ingestedPath;
    } else {
        return NextResponse.json({
            error: `No agent found for "${slug}". Please build the demo agent first.`
        }, { status: 404 });
    }

    try {
        // Load available files
        const kbPath = path.join(clientDir, 'knowledge_base.txt');
        const systemPromptPath = path.join(clientDir, 'system_prompt.txt');
        const personaContextPath = path.join(clientDir, 'persona_context.txt');
        const rawDataPath = path.join(clientDir, 'raw_data.json');

        let knowledge_base = '';
        let system_prompt = '';
        let persona_context = '';
        let business_name = slug.replace(/_/g, ' ').replace(/-/g, ' ');

        if (fs.existsSync(kbPath)) {
            knowledge_base = fs.readFileSync(kbPath, 'utf-8');
        }
        if (fs.existsSync(systemPromptPath)) {
            system_prompt = fs.readFileSync(systemPromptPath, 'utf-8');
        }
        if (fs.existsSync(personaContextPath)) {
            persona_context = fs.readFileSync(personaContextPath, 'utf-8');
        }
        if (fs.existsSync(rawDataPath)) {
            const rawData = JSON.parse(fs.readFileSync(rawDataPath, 'utf-8'));
            if (rawData.business_name) {
                business_name = rawData.business_name;
            }
        }

        return NextResponse.json({
            slug,
            business_name,
            knowledge_base,
            system_prompt,
            persona_context,
            // This would be used to inject into Tavus
            tavus_context: {
                custom_greeting: `Hello! I'm the AI assistant for ${business_name}. How can I help you today?`,
                context: persona_context || system_prompt,
                knowledge: knowledge_base
            }
        });

    } catch (error: any) {
        console.error("Demo API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
