import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(req: Request) {
    try {
        const missionsDir = path.join(process.cwd(), '..', 'intelligence', 'missions');

        if (!fs.existsSync(missionsDir)) {
            return NextResponse.json({ sessions: [] });
        }

        const files = fs.readdirSync(missionsDir)
            .filter(f => f.endsWith('.json'))
            .map(f => {
                const stats = fs.statSync(path.join(missionsDir, f));
                return {
                    filename: f,
                    name: f.replace('.json', '').split('_').slice(1).join('_'), // Removing timestamp
                    date: stats.mtime.toISOString()
                };
            })
            .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        return NextResponse.json({ sessions: files });

    } catch (error: any) {
        console.error("List History Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
