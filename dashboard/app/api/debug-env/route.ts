
import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        has_github_token: !!process.env.GITHUB_TOKEN,
        factory_repo: process.env.FACTORY_REPO,
        node_env: process.env.NODE_ENV,
        cwd: process.cwd(),
    });
}
