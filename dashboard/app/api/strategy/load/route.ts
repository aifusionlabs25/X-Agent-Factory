import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(req: Request) {
    try {
        const { filename } = await req.json();

        if (!filename) {
            return NextResponse.json({ error: 'Filename required' }, { status: 400 });
        }

        const missionsDir = path.join(process.cwd(), '..', 'intelligence', 'missions');
        const filePath = path.join(missionsDir, filename);

        if (!fs.existsSync(filePath)) {
            return NextResponse.json({ error: 'Session file not found' }, { status: 404 });
        }

        const content = fs.readFileSync(filePath, 'utf-8');
        const messages = JSON.parse(content);

        return NextResponse.json({ success: true, messages });

    } catch (error: any) {
        console.error("Load History Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
