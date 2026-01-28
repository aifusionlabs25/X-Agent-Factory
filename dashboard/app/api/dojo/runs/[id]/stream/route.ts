import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');

function findLogFile(runId: string) {
    const LOGS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'dojo_logs');
    if (!fs.existsSync(LOGS_DIR)) return null;
    const clients = fs.readdirSync(LOGS_DIR).filter(f => fs.statSync(path.join(LOGS_DIR, f)).isDirectory());
    for (const client of clients) {
        const potentialPath = path.join(LOGS_DIR, client, `${runId}.txt`);
        if (fs.existsSync(potentialPath)) {
            return { path: potentialPath, client };
        }
    }
    return null;
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const { id: runId } = await params;

    // Wait for file creation (Race condition fix)
    let logInfo = findLogFile(runId);
    let attempts = 0;
    while (!logInfo && attempts < 20) { // Wait up to 10s (20 * 500ms)
        await new Promise(r => setTimeout(r, 500));
        logInfo = findLogFile(runId);
        attempts++;
    }

    if (!logInfo) {
        return new NextResponse("Log not found (Timeout)", { status: 404 });
    }

    const encoder = new TextEncoder();

    const stream = new ReadableStream({
        async start(controller) {
            let currentSize = 0;
            const logPath = logInfo.path;

            // Poll for changes
            const interval = setInterval(() => {
                if (!fs.existsSync(logPath)) return;

                const stat = fs.statSync(logPath);
                if (stat.size > currentSize) {
                    const fd = fs.openSync(logPath, 'r');
                    const buffer = Buffer.alloc(stat.size - currentSize);
                    fs.readSync(fd, buffer, 0, buffer.length, currentSize);
                    fs.closeSync(fd);

                    const chunk = buffer.toString('utf-8');
                    // Format as SSE
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
                    currentSize = stat.size;

                    // Check for end?
                    if (chunk.includes("SIMULATION COMPLETE") || chunk.includes("[LOOP BREAK]")) {
                        controller.enqueue(encoder.encode(`event: close\ndata: {}\n\n`));
                        clearInterval(interval);
                        controller.close();
                    }
                }
            }, 1000);

            // Timeout safety?
            req.signal.onabort = () => {
                clearInterval(interval);
                controller.close();
            };
        }
    });

    return new NextResponse(stream, {
        headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        },
    });
}
