import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';
import fs from 'fs';

const execPromise = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { url, title, pain, demo } = await req.json();

        if (!url) {
            return NextResponse.json({ error: 'URL is required' }, { status: 400 });
        }

        const safeTitle = title || 'Unknown Business';
        const safePain = pain || '';
        const safeDemo = demo || '';

        // Run lead_enricher.py
        const command = `python tools/lead_enricher.py "${url}" --title "${safeTitle}" --pain "${safePain}" --demo "${safeDemo}"`;
        const cwd = path.join(process.cwd(), '..');

        console.log("Running enricher:", command);

        const { stdout, stderr } = await execPromise(command, { cwd, timeout: 120000 });
        console.log("Enricher Output:", stdout);

        if (stderr) {
            console.warn("Enricher Stderr:", stderr);
        }

        // Find and return the enriched data
        let slug = safeTitle.toLowerCase();
        slug = slug.replace(/[^a-z0-9\s]/g, '').trim().replace(/\s+/g, '_').slice(0, 50);

        const enrichedPath = path.join(cwd, 'intelligence', 'leads', `${slug}_enriched.json`);

        if (fs.existsSync(enrichedPath)) {
            const enrichedData = JSON.parse(fs.readFileSync(enrichedPath, 'utf-8'));
            return NextResponse.json({ success: true, enriched: enrichedData, logs: stdout });
        } else {
            return NextResponse.json({ success: true, logs: stdout, message: 'Enrichment complete but file not found' });
        }

    } catch (error: any) {
        console.error("Enrich API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
