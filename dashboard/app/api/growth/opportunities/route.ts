import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

/**
 * GET /api/growth/opportunities
 * 
 * Read-only endpoint that serves data from intelligence/daily_opportunities.json
 * Used by the Growth Radar dashboard card.
 * 
 * GUARDRAILS:
 * - Read-only: No mutations, no triggers, no side effects
 * - Returns empty array if file doesn't exist
 */
export async function GET() {
    try {
        // Path to opportunities file (relative to project root)
        const opportunitiesPath = path.join(
            process.cwd(),
            '..',
            'intelligence',
            'daily_opportunities.json'
        );

        // Check if file exists
        if (!fs.existsSync(opportunitiesPath)) {
            return NextResponse.json({
                generated_at: null,
                total_found: 0,
                top_count: 0,
                weekly_target: 5,
                prospects: [],
                message: "No opportunities data yet. Run growth_runner.py to populate."
            });
        }

        // Read and parse file
        const fileContent = fs.readFileSync(opportunitiesPath, 'utf-8');
        const data = JSON.parse(fileContent);

        return NextResponse.json(data);

    } catch (error) {
        console.error('Error reading opportunities:', error);
        return NextResponse.json(
            { error: 'Failed to read opportunities data' },
            { status: 500 }
        );
    }
}
