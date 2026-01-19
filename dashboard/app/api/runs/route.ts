import { NextResponse } from 'next/server';
import { getLatestRuns } from '../../lib/factory-data';

/**
 * GET /api/runs
 * Fetches latest runs from X-Agent-Factory
 */
export async function GET() {
    try {
        const runs = await getLatestRuns();

        const successful = runs.filter(r => r.success);
        const failed = runs.filter(r => !r.success);

        // Find latest run
        const latest = runs.length > 0
            ? runs.sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0]
            : null;

        return NextResponse.json({
            success: true,
            count: runs.length,
            successful_count: successful.length,
            failed_count: failed.length,
            latest_timestamp: latest?.timestamp || null,
            runs,
        });
    } catch (e: any) {
        console.error('[/api/runs] Error:', e);
        return NextResponse.json({
            success: false,
            error: e.message,
            runs: [],
        }, { status: 500 });
    }
}
