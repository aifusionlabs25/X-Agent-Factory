import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST() {
    const rootDir = path.resolve(process.cwd(), '..');
    const dbPath = path.join(rootDir, 'growth', 'db', 'growth.db');

    // Command: python tools/ingest_outcomes.py --db growth/db/growth.db --batch
    const command = `python tools/ingest_outcomes.py --db "${dbPath}" --batch`;

    return new Promise((resolve) => {
        exec(command, { cwd: rootDir }, (error, stdout, stderr) => {
            if (error) {
                resolve(NextResponse.json({ success: false, error: error.message, stderr }));
            } else {
                resolve(NextResponse.json({ success: true, stdout }));
            }
        });
    });
}
