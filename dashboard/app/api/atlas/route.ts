import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
    try {
        const cwd = path.join(process.cwd(), '..');
        const atlasPath = path.join(cwd, 'Grok_intelligence', 'market_atlas.json');

        if (!fs.existsSync(atlasPath)) {
            return NextResponse.json({ error: 'Market Atlas not found' }, { status: 404 });
        }

        let content = fs.readFileSync(atlasPath, 'utf-8');

        // Remove JS-style comments (// ...) before parsing
        content = content.replace(/\/\/.*$/gm, '');

        const atlas = JSON.parse(content);

        // Sort by ROI potential (deal_size_mrr * tam_us) descending
        const sorted = atlas.sort((a: any, b: any) => {
            const roiA = (a.deal_size_mrr || 0) * (a.tam_us || 0);
            const roiB = (b.deal_size_mrr || 0) * (b.tam_us || 0);
            return roiB - roiA;
        });

        // Add computed ROI field and suggested template
        const enriched = sorted.map((entry: any) => ({
            ...entry,
            roi_potential: (entry.deal_size_mrr || 0) * (entry.tam_us || 0),
            suggested_template: getSuggestedTemplate(entry.vertical, entry.sub_vertical)
        }));

        return NextResponse.json(enriched);

    } catch (error: any) {
        console.error("Atlas API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

function getSuggestedTemplate(vertical: string, subVertical: string): string {
    const v = (vertical || '').toLowerCase();
    const sv = (subVertical || '').toLowerCase();

    if (v.includes('home services') || sv.includes('hvac') || sv.includes('plumb') || sv.includes('roof')) {
        return 'Noah (Dispatch)';
    }
    if (v.includes('veterinary') || sv.includes('vet')) {
        return 'Ava (Triage)';
    }
    if (v.includes('legal') || sv.includes('law') || sv.includes('attorney')) {
        return 'Liam (Intake)';
    }
    if (v.includes('dental') || sv.includes('dentist')) {
        return 'Sage (Scheduler)';
    }
    if (v.includes('healthcare') || v.includes('urgent care') || sv.includes('medspa')) {
        return 'Ava (Triage)';
    }
    if (v.includes('real estate') || v.includes('property')) {
        return 'Rex (Leasing)';
    }
    if (v.includes('insurance')) {
        return 'Quinn (Quote)';
    }
    if (v.includes('hospitality') || sv.includes('hotel')) {
        return 'Concierge';
    }
    return 'Custom X Agent';
}
