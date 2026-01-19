import { NextResponse } from 'next/server';
import { getFactoryState } from '../../lib/factory-data';

/**
 * GET /api/state
 * Aggregates factory state: counts, scores, timestamps
 */
export async function GET() {
    try {
        const state = await getFactoryState();

        return NextResponse.json({
            success: true,
            timestamp: new Date().toISOString(),
            ...state,
        });
    } catch (e: any) {
        console.error('[/api/state] Error:', e);
        return NextResponse.json({
            success: false,
            error: e.message,
            active_verticals: 0,
            pipeline_score: 0,
            agents_deployed: 0,
            agents_total: 0,
            last_run_timestamp: null,
            qualified_leads: 0,
            opportunities: [],
            agents: [],
        }, { status: 500 });
    }
}
