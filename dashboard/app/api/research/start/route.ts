import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const JOBS_FILE = path.join(process.cwd(), '..', 'intelligence', 'research_jobs.json');

async function loadJobs(): Promise<any[]> {
    try {
        const data = await fs.readFile(JOBS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch {
        return [];
    }
}

async function saveJobs(jobs: any[]) {
    await fs.mkdir(path.dirname(JOBS_FILE), { recursive: true });
    await fs.writeFile(JOBS_FILE, JSON.stringify(jobs, null, 2));
}

function generateJobId(): string {
    return `research_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { agent_id, query, sources, max_depth = 3, max_pages = 100 } = body;

        if (!agent_id || !query) {
            return NextResponse.json({
                success: false,
                error: 'Missing agent_id or query'
            }, { status: 400 });
        }

        const jobId = generateJobId();

        // Create job record
        const job = {
            id: jobId,
            agent: agent_id,
            query: query,
            sources: sources || [],
            status: 'pending',
            progress: 0,
            documentsFound: 0,
            startedAt: new Date().toISOString(),
            config: {
                max_depth,
                max_pages
            }
        };

        // Save job
        const jobs = await loadJobs();
        jobs.unshift(job);
        await saveJobs(jobs);

        // Trigger Python research script in background
        const pythonScript = path.join(process.cwd(), '..', 'tools', 'deep_researcher.py');
        const outputDir = path.join(process.cwd(), '..', 'intelligence', 'research', jobId);

        // Create output directory
        await fs.mkdir(outputDir, { recursive: true });

        // Build command
        const command = `python "${pythonScript}" --job-id "${jobId}" --query "${query.replace(/"/g, '\\"')}" --agent "${agent_id}" --max-depth ${max_depth} --max-pages ${max_pages} --output "${outputDir}"`;

        // Run in background (non-blocking)
        exec(command, async (error, stdout, stderr) => {
            // Update job status on completion
            const currentJobs = await loadJobs();
            const jobIndex = currentJobs.findIndex(j => j.id === jobId);

            if (jobIndex >= 0) {
                if (error) {
                    currentJobs[jobIndex].status = 'error';
                    currentJobs[jobIndex].error = error.message;
                } else {
                    currentJobs[jobIndex].status = 'complete';
                    currentJobs[jobIndex].progress = 100;
                    currentJobs[jobIndex].completedAt = new Date().toISOString();

                    // Count documents in output
                    try {
                        const files = await fs.readdir(outputDir);
                        currentJobs[jobIndex].documentsFound = files.length;
                    } catch { }
                }
                await saveJobs(currentJobs);
            }
        });

        // Update job to running
        job.status = 'running';
        const updatedJobs = await loadJobs();
        const idx = updatedJobs.findIndex(j => j.id === jobId);
        if (idx >= 0) {
            updatedJobs[idx].status = 'running';
            await saveJobs(updatedJobs);
        }

        return NextResponse.json({
            success: true,
            job_id: jobId,
            estimated_time: `${Math.ceil(max_pages / 10)} minutes`
        });

    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
