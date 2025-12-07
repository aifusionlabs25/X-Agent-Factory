import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import util from 'util';

const execPromise = util.promisify(exec);

export async function POST() {
    try {
        // Resolve paths
        const factoryRoot = path.resolve(process.cwd(), '..'); // Assuming dashboard is in factory root/dashboard
        const scriptPath = path.join(factoryRoot, 'tools', 'market_scout.py');

        console.log(`🔍 Executing Scout: python "${scriptPath}"`);

        // Execute Python script
        const { stdout, stderr } = await execPromise(`python "${scriptPath}"`, {
            cwd: factoryRoot // Run from factory root so imports work
        });

        if (stderr) {
            console.warn('Scout Stderr:', stderr);
        }

        console.log('Scout Output:', stdout);

        // Read the generated JSON result directly to ensure we return the latest data
        const jsonPath = path.join(factoryRoot, 'intelligence', 'daily_opportunities.json');
        if (fs.existsSync(jsonPath)) {
            const data = fs.readFileSync(jsonPath, 'utf-8');
            const json = JSON.parse(data);
            return NextResponse.json({ success: true, data: json, logs: stdout });
        } else {
            return NextResponse.json({ success: true, logs: stdout, message: "Scout ran, but JSON not found." });
        }

    } catch (error: any) {
        console.error('Scout Error:', error);
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function GET() {
    // Just read the existing file
    try {
        const factoryRoot = path.resolve(process.cwd(), '..');
        const jsonPath = path.join(factoryRoot, 'intelligence', 'daily_opportunities.json');

        if (fs.existsSync(jsonPath)) {
            const data = fs.readFileSync(jsonPath, 'utf-8');
            const json = JSON.parse(data);
            // Ensure it's an array for the frontend
            const opportunities = Array.isArray(json) ? json : (json.top_opportunities || json.opportunities || []);
            return NextResponse.json(opportunities);
        }
        return NextResponse.json([]);
    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
