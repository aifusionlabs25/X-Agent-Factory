import { NextResponse } from 'next/server';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') });

/**
 * GET /api/workflow-status?run_id=...
 * Get detailed workflow status including jobs and steps
 */
export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const runId = searchParams.get('run_id');

    if (!runId) {
        return NextResponse.json({
            success: false,
            error: 'run_id parameter required',
        }, { status: 400 });
    }

    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    const FACTORY_REPO = process.env.FACTORY_REPO || 'aifusionlabs25/X-Agent-Factory';

    if (!GITHUB_TOKEN) {
        return NextResponse.json({
            success: false,
            error: 'GitHub token not configured',
        }, { status: 500 });
    }

    try {
        // Get run info
        const runUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/runs/${runId}`;
        const runResponse = await fetch(runUrl, {
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        if (!runResponse.ok) {
            return NextResponse.json({
                success: false,
                error: `GitHub API error: ${runResponse.status}`,
            }, { status: 502 });
        }

        const runData = await runResponse.json();

        // Get jobs for this run
        const jobsUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/runs/${runId}/jobs`;
        const jobsResponse = await fetch(jobsUrl, {
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        let jobs: any[] = [];
        if (jobsResponse.ok) {
            const jobsData = await jobsResponse.json();
            jobs = (jobsData.jobs || []).map((job: any) => ({
                id: job.id,
                name: job.name,
                status: job.status,
                conclusion: job.conclusion,
                started_at: job.started_at,
                completed_at: job.completed_at,
                steps: (job.steps || []).map((step: any) => ({
                    name: step.name,
                    status: step.status,
                    conclusion: step.conclusion,
                    number: step.number,
                })),
            }));
        }

        // Calculate overall progress
        const allSteps = jobs.flatMap(j => j.steps || []);
        const completedSteps = allSteps.filter((s: any) => s.status === 'completed');
        const progress = allSteps.length > 0 ? Math.round((completedSteps.length / allSteps.length) * 100) : 0;

        // Determine current step
        const inProgressStep = allSteps.find((s: any) => s.status === 'in_progress');
        const currentStep = inProgressStep?.name || (runData.status === 'completed' ? 'Complete' : 'Waiting...');

        return NextResponse.json({
            success: true,
            run: {
                id: runData.id,
                status: runData.status,
                conclusion: runData.conclusion,
                html_url: runData.html_url,
                created_at: runData.created_at,
                updated_at: runData.updated_at,
            },
            jobs,
            progress: {
                percentage: progress,
                completedSteps: completedSteps.length,
                totalSteps: allSteps.length,
                currentStep,
            },
        });

    } catch (e: any) {
        return NextResponse.json({
            success: false,
            error: e.message,
        }, { status: 500 });
    }
}
