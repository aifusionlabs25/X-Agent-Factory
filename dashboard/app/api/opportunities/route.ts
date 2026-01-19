import { NextResponse } from 'next/server';
import { getOpportunities } from '../../lib/factory-data';

/**
 * GET /api/opportunities
 * Fetches opportunities from X-Agent-Factory intelligence data
 */
export async function GET() {
    try {
        const opportunities = await getOpportunities();

        return NextResponse.json({
            success: true,
            count: opportunities.length,
            opportunities,
        });
    } catch (e: any) {
        console.error('[/api/opportunities] Error:', e);
        return NextResponse.json({
            success: false,
            error: e.message,
            opportunities: [],
        }, { status: 500 });
    }
}
