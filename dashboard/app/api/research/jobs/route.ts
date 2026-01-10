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

export async function GET(request: NextRequest) {
    try {
        const jobs = await loadJobs();
        return NextResponse.json({ jobs });
    } catch (error: any) {
        return NextResponse.json({
            jobs: [],
            error: error.message
        }, { status: 500 });
    }
}
