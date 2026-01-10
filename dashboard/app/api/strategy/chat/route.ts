import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const OLLAMA_URL = "http://localhost:11434/api/generate";

// The Chairperson Persona (Router) - Improved for reliability
const CHAIRPERSON_PROMPT = `You are a routing system. Analyze the user message and select which AI specialists should respond.

AVAILABLE SPECIALISTS:
Nova = Market research, data, verticals, TAM
Eve = Psychology, emotions, customer insights
Fin = Sales strategy, pricing, ROI, revenue
Troy = System prompts, architecture, technical
Sparkle = Copywriting, emails, marketing text
Sasha = Design, visuals, branding, UI/UX
Marcus = Legal, compliance, risk

RULES:
- For brainstorming/campaign/GTM queries: Select 3-4 agents
- For specific questions: Select 1-2 agents
- Always return a valid JSON array of agent names

USER MESSAGE: `;

export async function POST(req: Request) {
    try {
        const { message, persona, history, factoryMode, roundtable } = await req.json();

        if (!message) {
            return NextResponse.json({ error: 'Message required' }, { status: 400 });
        }

        const councilDir = path.join(process.cwd(), '..', 'intelligence', 'council');
        const intelligenceDir = path.join(process.cwd(), '..', 'intelligence');

        // Load the foundational COUNCIL_CONTEXT (shared knowledge for ALL agents)
        let councilContext = '';
        const councilContextPath = path.join(intelligenceDir, 'COUNCIL_CONTEXT.txt');
        if (fs.existsSync(councilContextPath)) {
            councilContext = fs.readFileSync(councilContextPath, 'utf-8');
        }

        // helper to get prompt
        const getAgentPrompt = (name: string) => {
            const p = path.join(councilDir, `${name}.txt`);
            if (fs.existsSync(p)) return fs.readFileSync(p, 'utf-8');
            return "";
        };

        // ROUNDTABLE CONTEXT: Injected for multi-agent discussions
        const ROUNDTABLE_CONTEXT = `
[ROUNDTABLE SESSION ACTIVE]
You are in a live Council meeting. Multiple specialists are responding.
- Build upon what previous agents said (their messages appear in history).
- Be concise (2-4 paragraphs max).
- Add your unique perspective based on your specialty.
- Do NOT ask the user to "click on" other agents - they are already in the room.
- End with a clear recommendation or insight.
`;

        // helper to call ollama
        const callAgent = async (name: string, inputMsg: string, agentHistory: any[], isRoundtable: boolean) => {
            // Start with the foundational context, then add the agent-specific prompt
            let sysInfo = councilContext + "\n\n" + getAgentPrompt(name);

            // Add roundtable context if applicable
            if (isRoundtable) {
                sysInfo += "\n\n" + ROUNDTABLE_CONTEXT;
            }

            if (name === 'Nova') {
                const atlasPath = path.join(intelligenceDir, 'market_atlas.json');
                if (fs.existsSync(atlasPath)) {
                    sysInfo += `\n\n[MARKET ATLAS DATA]\n${fs.readFileSync(atlasPath, 'utf-8').substring(0, 5000)}...`;
                }
            }

            let fullPrompt = `<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n${sysInfo}<|eot_id|>`;
            if (agentHistory && Array.isArray(agentHistory)) {
                agentHistory.forEach((msg: any) => {
                    const role = msg.role === 'user' ? 'user' : 'assistant';
                    // Tag assistant messages with persona if known
                    const content = msg.persona ? `[${msg.persona}]: ${msg.content}` : msg.content;
                    fullPrompt += `<|start_header_id|>${role}<|end_header_id|>\n\n${content}<|eot_id|>`;
                });
            }

            let finalMsg = inputMsg;
            if (factoryMode) {
                finalMsg = `[[FACTORY_MODE]] ${inputMsg}`;
            }

            fullPrompt += `<|start_header_id|>user<|end_header_id|>\n\n${finalMsg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n`;

            const res = await fetch(OLLAMA_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: "llama3",
                    prompt: fullPrompt,
                    stream: false,
                    options: { num_ctx: 8192 }
                })
            });
            const d = await res.json();
            return d.response;
        };

        // --- ROUNDTABLE MODE ---
        if (roundtable) {
            console.log("[ROUNDTABLE] Mode active. Routing query...");

            // Step 1: Chairperson Selects Agents
            const routerPrompt = CHAIRPERSON_PROMPT + `"${message}"\n\nRespond with ONLY a JSON array like ["Nova", "Fin"]. No other text.`;

            const routerRes = await fetch(OLLAMA_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: "llama3",
                    prompt: routerPrompt,
                    stream: false,
                    options: { num_ctx: 2048, temperature: 0.1 } // Low temp for deterministic output
                })
            });
            const routerData = await routerRes.json();
            console.log("[ROUNDTABLE] Router raw response:", routerData.response);

            let selectedAgents: string[] = [];
            try {
                // Try to extract JSON array from response
                const jsonMatch = routerData.response.match(/\[.*?\]/s);
                if (jsonMatch) {
                    selectedAgents = JSON.parse(jsonMatch[0]);
                }

                // Validate agent names
                const validAgents = ['Nova', 'Eve', 'Fin', 'Troy', 'Sparkle', 'Sasha', 'Marcus', 'Quinn', 'Nia', 'Rhea', 'WebWorker'];
                selectedAgents = selectedAgents.filter(a => validAgents.includes(a));

                if (selectedAgents.length === 0) {
                    // Fallback: For brainstorming, use a default squad
                    const lowerMsg = message.toLowerCase();
                    if (lowerMsg.includes('brainstorm') || lowerMsg.includes('gtm') || lowerMsg.includes('campaign') || lowerMsg.includes('strategy')) {
                        selectedAgents = ['Nova', 'Fin', 'Eve', 'Sparkle'];
                    } else {
                        selectedAgents = [persona || 'Nova'];
                    }
                }
            } catch (e) {
                console.log("[ROUNDTABLE] JSON parse failed, using fallback.");
                selectedAgents = ['Nova', 'Fin', 'Eve']; // Default brainstorm squad
            }

            console.log("[ROUNDTABLE] Selected agents:", selectedAgents);

            // Step 2: Run Selected Agents (Sequential)
            const replies = [];
            const sharedHistory = [...(history || [])];

            for (const agent of selectedAgents) {
                console.log(`[ROUNDTABLE] Calling agent: ${agent}`);
                const reply = await callAgent(agent, message, sharedHistory, true);
                replies.push({
                    role: 'assistant',
                    content: reply,
                    persona: agent
                });
                // Add to history so next agent sees it
                sharedHistory.push({ role: 'assistant', content: reply, persona: agent });
            }

            console.log(`[ROUNDTABLE] Completed. ${replies.length} agents responded.`);
            return NextResponse.json({ roundtable: true, replies });

        } else {
            // --- STANDARD MODE (1-on-1) ---
            const reply = await callAgent(persona, message, history, false);
            return NextResponse.json({ reply });
        }

    } catch (error: any) {
        console.error("Strategy API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
