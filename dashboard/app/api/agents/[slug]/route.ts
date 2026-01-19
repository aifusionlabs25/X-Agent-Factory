import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

const FACTORY_ROOT = path.resolve(process.cwd(), '..');
const AGENTS_DIR = path.join(FACTORY_ROOT, 'agents');
const INGESTED_DIR = path.join(FACTORY_ROOT, 'ingested_clients');

export async function DELETE(
    request: NextRequest,
    { params }: { params: { slug: string } }
) {
    const { slug } = params;

    if (!slug) {
        return NextResponse.json({ error: 'Agent slug is required' }, { status: 400 });
    }

    // Security: prevent directory traversal
    if (slug.includes('..') || slug.includes('/') || slug.includes('\\')) {
        return NextResponse.json({ error: 'Invalid slug' }, { status: 400 });
    }

    const agentPath = path.join(AGENTS_DIR, slug);
    const ingestedPath = path.join(INGESTED_DIR, slug.replace('_legal_m', '_l').replace('_solar_solutions', '_s').replace('_air_co', '_a')); // Basic heuristic for now, or just try explicit delete

    // Note: The ingested path heuristic is tricky because of the name truncation we saw earlier.
    // For safety, we will primarily try to delete the exact match in ingested_clients 
    // OR rely on a list if we had one. 
    // Given the earlier issue: agents/ai_answering_service_for_home_services_legal_m 
    // vs ingested_clients/ai_answering_service_for_home_services_l
    // A better approach might be to just try deleting the folder if it exists in agents/, 
    // and then ideally we'd need to know the 'dossier' path to delete the ingested part correctly.
    // For now, let's delete the AGENT folder (which is what shows in the UI list). 
    // That cleans up the view. Deleting the ingested data is a "nice to have" deep clean 
    // but arguably distinct (source data vs built agent).
    // Let's stick to deleting the agent folder for the UI feature "Delete Agent".

    try {
        // Check if agent exists
        try {
            await fs.access(agentPath);
        } catch {
            return NextResponse.json({ error: 'Agent not found' }, { status: 404 });
        }

        // Delete agent directory
        await fs.rm(agentPath, { recursive: true, force: true });

        // Attempt rudimentary cleanup of ingested folder if name matches exactly or closely?
        // Let's keep it safe and just delete the agent for now. 
        // If the user wants to "Deep Clean", that's a bigger feature.

        return NextResponse.json({ success: true, message: `Agent ${slug} deleted` });
    } catch (error) {
        console.error('Delete error:', error);
        return NextResponse.json({ error: 'Failed to delete agent' }, { status: 500 });
    }
}
