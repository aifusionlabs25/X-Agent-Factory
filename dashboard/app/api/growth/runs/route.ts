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

    // Detect time column for sorting
    const columns = await db.all("PRAGMA table_info(search_runs)");
    const colNames = columns.map((c: any) => c.name);

    let sortCol = 'rowid';
    if (colNames.includes('timestamp')) sortCol = 'timestamp';
    else if (colNames.includes('started_at')) sortCol = 'started_at';
    else if (colNames.includes('created_at')) sortCol = 'created_at';
    else if (colNames.includes('run_ts')) sortCol = 'run_ts';

    // ORDER BY dynamic column
    // Normalize timestamp to 'created_at' for UI consistency
    // Check if place_runs exists (G5.0 Schema)
    const tableCheck = await db.get("SELECT name FROM sqlite_master WHERE type='table' AND name='place_runs'");
    const useWins = !!tableCheck;

    const runs = await db.all(`
          SELECT 
            sr.*, 
            sr.${sortCol} as created_at
            ${useWins ? ", (SELECT COUNT(*) FROM place_runs pr JOIN place_status ps ON pr.place_id = ps.place_id WHERE pr.run_id = sr.run_id AND ps.status = 'won') as wins_count" : ""}
          FROM search_runs sr
          ORDER BY sr.${sortCol} DESC 
          LIMIT 20
        `);

    await db.close();

    return NextResponse.json({ success: true, runs });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
