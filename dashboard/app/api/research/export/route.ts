import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const JOBS_FILE = path.join(process.cwd(), '..', 'intelligence', 'research_jobs.json');

async function loadJobs(): Promise<any[]> {
    try {
        const data = await fs.readFile(JOBS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch {
        return [];
    }
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { job_id } = body;

        if (!job_id) {
            return NextResponse.json({
                success: false,
                error: 'Missing job_id'
            }, { status: 400 });
        }

        // Find job
        const jobs = await loadJobs();
        const job = jobs.find(j => j.id === job_id);

        if (!job) {
            return NextResponse.json({
                success: false,
                error: 'Job not found'
            }, { status: 404 });
        }

        // Get research output
        const researchDir = path.join(process.cwd(), '..', 'intelligence', 'research', job_id);
        const agentKBDir = path.join(process.cwd(), '..', 'agents', job.agent, 'knowledge_base');

        // Create KB directory
        await fs.mkdir(agentKBDir, { recursive: true });

        // Copy research files to KB
        let filesCreated = 0;
        try {
            const files = await fs.readdir(researchDir);

            for (const file of files) {
                if (file.endsWith('.json') || file.endsWith('.md') || file.endsWith('.txt')) {
                    const srcPath = path.join(researchDir, file);
                    const destPath = path.join(agentKBDir, file);
                    await fs.copyFile(srcPath, destPath);
                    filesCreated++;
                }
            }

            // Create KB index file
            const indexPath = path.join(agentKBDir, 'KB_INDEX.json');
            const index = {
                agent: job.agent,
                source_job: job_id,
                query: job.query,
                files: files.filter(f => f.endsWith('.json') || f.endsWith('.md') || f.endsWith('.txt')),
                exported_at: new Date().toISOString(),
                total_files: filesCreated
            };
            await fs.writeFile(indexPath, JSON.stringify(index, null, 2));
            filesCreated++;

        } catch (e: any) {
            return NextResponse.json({
                success: false,
                error: `Failed to read research output: ${e.message}`
            }, { status: 500 });
        }

        return NextResponse.json({
            success: true,
            files_created: filesCreated,
            output_path: agentKBDir
        });

    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
