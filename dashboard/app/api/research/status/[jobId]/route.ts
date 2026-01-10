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

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ jobId: string }> }
) {
    try {
        // Await params (Next.js 14+ requirement)
        const { jobId } = await params;

        const jobs = await loadJobs();
        const job = jobs.find(j => j.id === jobId);

        if (!job) {
            return NextResponse.json({
                success: false,
                error: 'Job not found'
            }, { status: 404 });
        }

        // Check output directory for progress
        const outputDir = path.join(process.cwd(), '..', 'intelligence', 'research', jobId);
        try {
            const files = await fs.readdir(outputDir);
            job.documentsFound = files.filter(f => f.endsWith('.json') || f.endsWith('.md')).length;

            // Update progress based on files
            if (job.status === 'running') {
                const maxPages = job.config?.max_pages || 100;
                job.progress = Math.min(95, Math.floor((job.documentsFound / maxPages) * 100));
            }
        } catch {
            // Output dir doesn't exist yet
        }

        return NextResponse.json({ job });
    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
