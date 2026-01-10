import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const OLLAMA_URL = "http://localhost:11434/api/generate";

export async function POST(req: Request) {
    try {
        const { message, slug } = await req.json();

        if (!message || !slug) {
            return NextResponse.json({ error: 'Message and Slug required' }, { status: 400 });
        }

        // Locate Agent Assets
        const agentDir = path.join(process.cwd(), '..', 'intelligence', 'agents', slug);

        if (!fs.existsSync(agentDir)) {
            return NextResponse.json({ error: 'Agent not found. Have you built it?' }, { status: 404 });
        }

        // Load Context
        let systemPrompt = "You are a helpful AI assistant.";
        if (fs.existsSync(path.join(agentDir, 'system_prompt.txt'))) {
            systemPrompt = fs.readFileSync(path.join(agentDir, 'system_prompt.txt'), 'utf-8');
        }

        let personaContext = "";
        if (fs.existsSync(path.join(agentDir, 'persona_context.txt'))) {
            personaContext = fs.readFileSync(path.join(agentDir, 'persona_context.txt'), 'utf-8');
        }

        let knowledgeBase = "";
        if (fs.existsSync(path.join(agentDir, 'knowledge_base.txt'))) {
            knowledgeBase = fs.readFileSync(path.join(agentDir, 'knowledge_base.txt'), 'utf-8');
        }

        // Construct Full Prompt
        // Combining System + Persona + KB + User Input
        const fullPrompt = `
        ${systemPrompt}
        
        [PERSONA CONTEXT]
        ${personaContext}
        
        [KNOWLEDGE BASE]
        ${knowledgeBase}
        
        [USER MESSAGE]
        ${message}
        
        [RESPONSE]
        `;

        // Call Ollama (Llama 3)
        const response = await fetch(OLLAMA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: "llama3",
                prompt: fullPrompt,
                stream: false
            })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        return NextResponse.json({ reply: data.response });

    } catch (error: any) {
        console.error("Chat API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
