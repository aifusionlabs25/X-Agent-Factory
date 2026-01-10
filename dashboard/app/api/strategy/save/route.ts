import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(req: Request) {
    try {
        const { messages, sessionName } = await req.json();

        if (!messages || !Array.isArray(messages)) {
            return NextResponse.json({ error: 'Messages array required' }, { status: 400 });
        }

        // Generate Filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const safeName = (sessionName || 'strategy_session').replace(/[^a-zA-Z0-9_-]/g, '_');
        const filename = `${timestamp}_${safeName}.json`;
        const mdFilename = `${timestamp}_${safeName}.md`;

        const missionsDir = path.join(process.cwd(), '..', 'intelligence', 'missions');
        if (!fs.existsSync(missionsDir)) {
            fs.mkdirSync(missionsDir, { recursive: true });
        }

        // Save JSON (Raw Data)
        const jsonPath = path.join(missionsDir, filename);
        fs.writeFileSync(jsonPath, JSON.stringify(messages, null, 2));

        // Save Markdown (Human Readable)
        let mdContent = `# Mission Log: ${safeName}\nDate: ${new Date().toLocaleString()}\n\n`;
        messages.forEach((msg: any) => {
            const role = msg.role.toUpperCase();
            const persona = msg.persona ? ` (${msg.persona})` : '';
            mdContent += `### ${role}${persona}\n\n${msg.content}\n\n---\n\n`;
        });

        const mdPath = path.join(missionsDir, mdFilename);
        fs.writeFileSync(mdPath, mdContent);

        return NextResponse.json({ success: true, filename: mdFilename });

    } catch (error: any) {
        console.error("Save Strategy Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
