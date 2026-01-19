import { NextResponse } from 'next/server';

/**
 * POST /api/new-prospect
 * Triggers the new_prospect workflow in the Factory repo via GitHub Actions.
 * 
 * Required env vars:
 *   GITHUB_TOKEN - Fine-grained PAT with Actions + Contents write access
 *   FACTORY_REPO - Owner/repo (e.g., aifusionlabs25/X-Agent-Factory)
 *   FACTORY_BRANCH - Branch name (e.g., main)
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { url, deployEnv = 'off' } = body;

        // Validate URL
        if (!url) {
            return NextResponse.json({
                success: false,
                error: 'URL is required',
            }, { status: 400 });
        }

        // Validate URL format
        try {
            new URL(url);
        } catch {
            return NextResponse.json({
                success: false,
                error: 'Invalid URL format',
            }, { status: 400 });
        }

        // Get env vars
        const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
        const FACTORY_REPO = process.env.FACTORY_REPO || 'aifusionlabs25/X-Agent-Factory';
        const FACTORY_BRANCH = process.env.FACTORY_BRANCH || 'main';

        if (!GITHUB_TOKEN) {
            return NextResponse.json({
                success: false,
                error: 'GitHub token not configured. Set GITHUB_TOKEN env var.',
            }, { status: 500 });
        }

        // Trigger workflow_dispatch
        const workflowUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/workflows/new_prospect.yml/dispatches`;

        const dispatchResponse = await fetch(workflowUrl, {
            method: 'POST',
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ref: FACTORY_BRANCH,
                inputs: {
                    url: url,
                    deploy_env: deployEnv,
                },
            }),
        });

        if (!dispatchResponse.ok) {
            const errorText = await dispatchResponse.text();
            console.error('[/api/new-prospect] GitHub API error:', errorText);
            return NextResponse.json({
                success: false,
                error: `GitHub API error: ${dispatchResponse.status}`,
                details: errorText,
            }, { status: 502 });
        }

        // Get the latest workflow run info
        const runsUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/workflows/new_prospect.yml/runs?per_page=1`;

        // Wait a moment for the workflow to be created
        await new Promise(resolve => setTimeout(resolve, 2000));

        const runsResponse = await fetch(runsUrl, {
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        let runInfo = null;
        if (runsResponse.ok) {
            const runsData = await runsResponse.json();
            if (runsData.workflow_runs && runsData.workflow_runs.length > 0) {
                const latestRun = runsData.workflow_runs[0];
                runInfo = {
                    id: latestRun.id,
                    status: latestRun.status,
                    html_url: latestRun.html_url,
                };
            }
        }

        return NextResponse.json({
            success: true,
            message: 'Workflow triggered successfully',
            url: url,
            deployEnv: deployEnv,
            workflow: runInfo,
        });

    } catch (e: any) {
        console.error('[/api/new-prospect] Error:', e);
        return NextResponse.json({
            success: false,
            error: e.message,
        }, { status: 500 });
    }
}

/**
 * GET /api/new-prospect?run_id=...
 * Check status of a workflow run
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
        const runUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/runs/${runId}`;

        const response = await fetch(runUrl, {
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
        });

        if (!response.ok) {
            return NextResponse.json({
                success: false,
                error: `GitHub API error: ${response.status}`,
            }, { status: 502 });
        }

        const data = await response.json();

        return NextResponse.json({
            success: true,
            run: {
                id: data.id,
                status: data.status,
                conclusion: data.conclusion,
                html_url: data.html_url,
                created_at: data.created_at,
                updated_at: data.updated_at,
            },
        });

    } catch (e: any) {
        return NextResponse.json({
            success: false,
            error: e.message,
        }, { status: 500 });
    }
}
