import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');
const LOGS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_logs');

export async function GET(req: NextRequest) {
    try {
        if (!fs.existsSync(LOGS_DIR)) {
            return NextResponse.json({ runs: [] });
        }

        // Iterate Client Directories
        const clients = fs.readdirSync(LOGS_DIR).filter(f => fs.statSync(path.join(LOGS_DIR, f)).isDirectory());

        let allRuns = [];

        for (const client of clients) {
            const clientDir = path.join(LOGS_DIR, client);
            const files = fs.readdirSync(clientDir);

            // Find logs (files ending in .txt but NOT .system_prompt.txt or .persona_context.txt)
            // Actually, easier to look for .score.json if we assume everything interesting has a score now.
            // But some old logs might not.
            // Let's filter for valid log files: YYYYMMDD_... .txt

            const runFiles = files.filter(f => f.endsWith('.txt') && !f.includes('.system_prompt.') && !f.includes('.persona_context.'));

            for (const logFile of runFiles) {
                const runId = logFile.replace('.txt', '');
                const scoreFile = runId + '.score.json';
                const logPath = path.join(clientDir, logFile);

                let metadata = {
                    run_id: runId,
                    client: client,
                    timestamp: fs.statSync(logPath).mtime,
                    verdict: 'UNKNOWN', // Default
                    score: 0
                };

                // Try load score
                if (fs.existsSync(path.join(clientDir, scoreFile))) {
                    try {
                        const scoreData = JSON.parse(fs.readFileSync(path.join(clientDir, scoreFile), 'utf-8'));
                        metadata.verdict = scoreData.verdict || 'UNKNOWN';
                        metadata.score = scoreData.score || 0;
                    } catch (e) {
                        console.error('Error parsing score:', scoreFile);
                    }
                }

                allRuns.push(metadata);
            }
        }

        // Sort by timestamp desc
        allRuns.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

        return NextResponse.json({ runs: allRuns });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
