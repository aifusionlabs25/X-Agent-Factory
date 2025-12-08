import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
    try {
        const { vertical, leads } = await request.json();

        if (!vertical || !leads || !Array.isArray(leads)) {
            return NextResponse.json({
                success: false,
                error: 'Missing vertical or leads data'
            }, { status: 400 });
        }

        // Sanitize vertical name for filename
        const sanitizedName = vertical
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, '')
            .trim()
            .replace(/\s+/g, '_')
            .slice(0, 50);

        const filename = `${sanitizedName}_qualified`;
        const leadsDir = path.join(process.cwd(), '..', 'intelligence', 'leads');

        // Ensure directory exists
        if (!fs.existsSync(leadsDir)) {
            fs.mkdirSync(leadsDir, { recursive: true });
        }

        // Save JSON
        const jsonPath = path.join(leadsDir, `${filename}.json`);
        fs.writeFileSync(jsonPath, JSON.stringify(leads, null, 2), 'utf-8');

        // Save CSV
        const csvPath = path.join(leadsDir, `${filename}.csv`);
        const headers = [
            'Business Name',
            'URL',
            'Nova Score',
            'Nova Reason',
            'Query Source',
            'Suggested Template',
            'Buyer Persona',
            'Deal Size MRR'
        ];

        const rows = leads.map((lead: any) => [
            lead.title || '',
            lead.href || '',
            lead.nova_score || '',
            (lead.nova_reason || '').replace(/"/g, '""'),
            lead.query_source || '',
            lead.suggested_template || '',
            lead.buyer_persona || '',
            lead.deal_size || ''
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map((row: string[]) => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        fs.writeFileSync(csvPath, csvContent, 'utf-8');

        console.log(`✅ Saved hunt results: ${filename}`);
        console.log(`   JSON: ${jsonPath}`);
        console.log(`   CSV: ${csvPath}`);

        return NextResponse.json({
            success: true,
            filename: filename,
            jsonPath: `intelligence/leads/${filename}.json`,
            csvPath: `intelligence/leads/${filename}.csv`,
            leadCount: leads.length
        });

    } catch (error: any) {
        console.error('Save hunt error:', error);
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
