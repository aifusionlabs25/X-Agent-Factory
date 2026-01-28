import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

// Helper to compute confidence
function getConfidence(lead: any) {
    let checks = 0;
    if (lead.website) checks++;
    if (lead.phone) checks++;
    if (lead.name) checks++;
    if (lead.formatted_address) checks++;

    if (checks >= 3) return 'High';
    if (checks === 2) return 'Medium';
    return 'Low';
}

// Helper to compute Playbook (TS port of playbook_engine.py)
function getPlaybook(lead: any) {
    const score = lead.score || 5; // Default if missing
    const hasPhone = !!lead.phone;
    const hasWebsite = !!lead.website;
    const rating = lead.rating || 0;
    const status = lead.status || 'new';

    let action = "Review";
    let channel = "Manual";
    let priority = "Normal";
    let reason = "Standard review needed.";
    let script = "";

    if (status === 'new') {
        if (score >= 8) {
            priority = "High";
            if (hasPhone) {
                action = "Call Now";
                channel = "Phone";
                reason = "High value lead with phone.";
                script = "Hi, I saw your high rating on Google...";
            } else if (hasWebsite) {
                action = "Visit Website";
                channel = "Web";
                reason = "Good lead, no phone.";
            } else {
                action = "Research";
                reason = "Verify existence.";
            }
        } else if (score >= 5) {
            priority = "Normal";
            if (hasPhone && rating < 4.0) {
                action = "Call (Reputation)";
                channel = "Phone";
                reason = "Pitch reputation management.";
            } else if (hasWebsite) {
                action = "Email";
                channel = "Email";
                reason = "Standard outreach.";
            } else {
                action = "Skip";
                reason = "Mid score, low data.";
            }
        } else {
            action = "Archive";
            priority = "Low";
            reason = "Low score.";
        }
    } else if (status === 'contacted') {
        action = "Follow Up";
        priority = "High";
        reason = "Lead contacted. Check for reply.";
    }

    return { action, channel, priority, reason, script };
}

export async function GET(request: Request, { params }: { params: { runId: string } }) {
    const dbPath = path.join(process.cwd(), '../growth/db/growth.db');
    const { runId } = params;

    try {
        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        // Fetch leads for run with status and details
        // Added lead_tasks join to see if there is a pending task
        const leads = await db.all(`
            SELECT 
                p.place_id,
                p.name,
                p.formatted_address,
                p.phone,
                p.website,
                p.rating,
                p.user_ratings_total,
                p.source,
                ps.status,
                ps.outcome_notes,
                ps.updated_at,
                ps.score, 
                pr.created_at as discovered_at,
                (SELECT count(*) FROM lead_tasks lt WHERE lt.place_id = p.place_id AND lt.status = 'pending') as pending_tasks
            FROM place_runs pr
            JOIN places p ON pr.place_id = p.place_id
            LEFT JOIN place_status ps ON p.place_id = ps.place_id
            WHERE pr.run_id = ?
            ORDER BY ps.status DESC, p.rating DESC
        `, runId);

        // Enrich with calculated logic
        const enriched = leads.map(l => {
            const confidence = getConfidence(l);
            const playbook = getPlaybook(l);

            // Score breakdown stub (since we don't track components in DB yet, we just reconstruct base)
            const scoreBreakdown = [
                `Base: 5`,
                l.website ? '+2 Website' : '-2 No Website',
                l.phone ? '+1 Phone' : '-1 No Phone',
                l.rating >= 4.5 ? '+1 High Rating' : (l.rating < 3.5 && l.rating > 0 ? '-1 Low Rating' : ''),
                // Confidence impact
                confidence === 'High' ? '+0 (High Conf)' : (confidence === 'Low' ? '-1 (Low Conf)' : '')
            ].filter(Boolean);

            return {
                ...l,
                confidence,
                playbook,
                score_breakdown: scoreBreakdown
            };
        });

        await db.close();

        return NextResponse.json({ success: true, leads: enriched });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
