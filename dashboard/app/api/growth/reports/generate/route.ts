
import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST() {
    try {
        const toolDir = path.join(process.cwd(), '..', 'tools');
        const scriptPath = path.join(toolDir, 'analysis_engine.py');

        return new Promise((resolve) => {
            const pythonProcess = spawn('python', [scriptPath, '--mode', 'generate']);

            let dataString = '';
            let errorString = '';

            pythonProcess.stdout.on('data', (data) => { dataString += data.toString(); });
            pythonProcess.stderr.on('data', (data) => { errorString += data.toString(); });

            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    console.error('Report Gen Failed:', errorString);
                    resolve(NextResponse.json({ success: false, error: 'Generation failed' }, { status: 500 }));
                } else {
                    try {
                        const data = JSON.parse(dataString);
                        resolve(NextResponse.json({ success: true, path: data.path }));
                    } catch (e) {
                        resolve(NextResponse.json({ success: false, error: 'Parse failed' }, { status: 500 }));
                    }
                }
            });
        });
    } catch (e) {
        return NextResponse.json({ success: false, error: 'Internal Error' }, { status: 500 });
    }
}
