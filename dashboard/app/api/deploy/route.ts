import { NextResponse } from 'next/server';

export const runtime = 'nodejs'; // Ensure not edge runtime

/**
 * POST /api/deploy
 * Dispatches the deploy_agent.yml workflow to deploy an agent via GitHub Actions.
 * 
 * Required env vars:
 *   GITHUB_TOKEN - Fine-grained PAT with Actions write access
 *   FACTORY_REPO - Owner/repo (e.g., aifusionlabs25/X-Agent-Factory)
 */
export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { slug, env = 'staging' } = body;

        // Validate slug
        if (!slug) {
            return NextResponse.json({
                success: false,
                error: 'Agent slug is required',
            }, { status: 400 });
        }

        // Get env vars
        const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
        const FACTORY_REPO = process.env.FACTORY_REPO || 'aifusionlabs25/X-Agent-Factory';

        if (!GITHUB_TOKEN) {
            return NextResponse.json({
                success: false,
                error: 'GitHub token not configured. Set GITHUB_TOKEN env var.',
            }, { status: 500 });
        }

        console.log(`🚀 Dispatching deploy workflow for: ${slug} → ${env}`);

        // Trigger workflow_dispatch
        const workflowUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/workflows/deploy_agent.yml/dispatches`;

        const dispatchResponse = await fetch(workflowUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ref: 'main',
                inputs: {
                    slug: slug,
                    env: env,
                },
            }),
        });

        if (!dispatchResponse.ok) {
            const errorText = await dispatchResponse.text();
            console.error('[/api/deploy] GitHub API error:', errorText);
            return NextResponse.json({
                success: false,
                error: `GitHub API error: ${dispatchResponse.status}`,
                details: errorText,
            }, { status: 502 });
        }

        // Get the latest workflow run info (dispatch is async, so we wait briefly)
        await new Promise(resolve => setTimeout(resolve, 2000));

        const runsUrl = `https://api.github.com/repos/${FACTORY_REPO}/actions/workflows/deploy_agent.yml/runs?per_page=1`;

        const runsResponse = await fetch(runsUrl, {
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
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
            message: `Deployment queued for ${slug}`,
            slug: slug,
            env: env,
            workflow: runInfo,
        });

    } catch (error: any) {
        console.error('[/api/deploy] Error:', error);
        return NextResponse.json({
            success: false,
            error: error.message,
        }, { status: 500 });
    }
}

/**
 * GET /api/deploy?run_id=...
 * Check status of a deploy workflow run
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
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
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
