import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

export async function GET() {
    const dbPath = path.join(process.cwd(), '../growth/db/growth.db');

    try {
        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        // Mirroring GrowthDB.get_weekly_stats logic in JS or just reading raw counts
        // For directness, let's just query the tables directly.

        const exported = await db.get("SELECT COUNT(*) as count FROM place_status WHERE status = 'exported'");
        const contacted = await db.get("SELECT COUNT(*) as count FROM place_status WHERE status = 'contacted'");
        const meetings = await db.get("SELECT COUNT(*) as count FROM place_status WHERE status = 'booked_meeting'");
        const won = await db.get("SELECT COUNT(*) as count FROM place_status WHERE status = 'won'");
        const dead = await db.get("SELECT COUNT(*) as count FROM place_status WHERE status = 'dead_end'");
        const dnc = await db.get("SELECT COUNT(*) as count FROM place_status WHERE status = 'do_not_contact'");

        await db.close();

        const stats = {
            total_exported: exported.count,
            total_contacted: contacted.count,
            meetings: meetings.count,
            won: won.count,
            suppressed: dead.count + dnc.count
        };

        return NextResponse.json({ success: true, stats });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: 'DB missing or error: ' + error.message });
    }
}
