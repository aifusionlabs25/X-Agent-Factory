import { NextResponse } from 'next/server';
import { getAgents } from '../../lib/factory-data';

/**
 * GET /api/agents
 * Lists deployed agents from X-Agent-Factory
 */
export async function GET() {
    try {
        const agents = await getAgents();

        const deployed = agents.filter(a => a.deployed);
        const pending = agents.filter(a => !a.deployed);

        return NextResponse.json({
            success: true,
            total: agents.length,
            deployed_count: deployed.length,
            pending_count: pending.length,
            agents,
        });
    } catch (e: any) {
        console.error('[/api/agents] Error:', e);
        return NextResponse.json({
            success: false,
            error: e.message,
            agents: [],
        }, { status: 500 });
    }
}
