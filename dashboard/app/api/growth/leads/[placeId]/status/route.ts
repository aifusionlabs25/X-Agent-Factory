import { NextResponse } from 'next/server';
import path from 'path';

// We need to import GrowthDB dynamically or interact via python shell if we couldn't run python logic directly?
// Wait, I am writing TypeScript API routes. I cannot import python classes directly.
// The previous implementations (runs/route.ts) accessed the SQLite DB DIRECTLY from Node/Next.js.
// So I must implement the "update logic" in TypeScript here, duplicating the logic in GrowthDB?
// OR I can use the `growth_db` python script via shell?
// The user "Context" says: "Growth DB: growth/db/growth.db".
// The existing `api/growth/runs/route.ts` uses `sqlite3` driver.
// My previous step 1 updated `growth_db.py` (Python) to add `log_activity`.
// But the UI calls the Next.js API (TypeScript).
// So the Next.js API *must* implement the DB write logic directly in TS, or call a python script.
// Given "Local-only deployment", calling python is valid, but slow/clunky for an interactive UI API.
// "Duplicate logic" in TS is cleaner for performance. 
// I will implement the equivalent of `update_outcome` + `log_activity` in TypeScript here.

import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

export async function POST(request: Request, { params }: { params: { placeId: string } }) {
    const dbPath = path.join(process.cwd(), '../growth/db/growth.db');
    const { placeId } = params;

    try {
        const body = await request.json();
        const { status, notes } = body;

        if (!status) {
            return NextResponse.json({ success: false, error: "Status required" }, { status: 400 });
        }

        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        const now = new Date().toISOString();

        // 1. Get current status for activity log
        const current = await db.get("SELECT status FROM place_status WHERE place_id = ?", placeId);
        const oldStatus = current ? current.status : null;

        // 2. Upsert place_status
        if (current) {
            await db.run(`
                UPDATE place_status 
                SET status = ?, outcome_notes = ?, updated_at = ? 
                WHERE place_id = ?
            `, status, notes || null, now, placeId);
        } else {
            await db.run(`
                INSERT INTO place_status (place_id, status, outcome_notes, updated_at, outcome_source)
                VALUES (?, ?, ?, ?, 'dashboard')
            `, placeId, status, notes || null, now);
        }

        // 3. Log Activity (Duplicate of GrowthDB.log_activity logic)
        // Check if table exists just in case migration failed (it shouldn't have)
        // We assume migration ran.
        await db.run(`
            INSERT INTO place_activity_log (place_id, action, old_value, new_value, notes, created_at)
            VALUES (?, 'status_change', ?, ?, ?, ?)
        `, placeId, oldStatus, status, notes || null, now);

        await db.close();

        return NextResponse.json({ success: true, status, notes });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
