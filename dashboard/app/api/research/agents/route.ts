import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
    try {
        // Scan agents directory for manifests
        const agentsDir = path.join(process.cwd(), '..', 'agents');
        const agents: any[] = [];

        try {
            const entries = await fs.readdir(agentsDir, { withFileTypes: true });

            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const manifestPath = path.join(agentsDir, entry.name, 'agent_manifest.json');
                    try {
                        const manifest = await fs.readFile(manifestPath, 'utf-8');
                        const data = JSON.parse(manifest);
                        agents.push({
                            agent_id: data.agent_id || entry.name,
                            agent_name: data.agent_name || entry.name,
                            vertical: data.vertical || 'Unknown',
                            status: data.status || 'unknown'
                        });
                    } catch (e) {
                        // Skip if no manifest
                    }
                }
            }
        } catch (e) {
            // Agents directory doesn't exist yet
        }

        // Fallback if no agents found
        if (agents.length === 0) {
            agents.push({
                agent_id: 'luna_veterinary',
                agent_name: 'Dr. Luna',
                vertical: 'Veterinary / After-Hours Pet Triage',
                status: 'deployed_testing'
            });
        }

        return NextResponse.json({ agents });
    } catch (error: any) {
        return NextResponse.json({
            agents: [],
            error: error.message
        }, { status: 500 });
    }
}
