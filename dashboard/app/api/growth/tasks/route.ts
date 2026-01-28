import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

export async function GET(request: Request) {
    const dbPath = path.join(process.cwd(), '../growth/db/growth.db');

    try {
        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        const { searchParams } = new URL(request.url);
        const status = searchParams.get('status');
        const limit = searchParams.get('limit') || 10;

        let query = `
            SELECT t.*, p.name as place_name, p.phone, p.website, ps.status as lead_status 
            FROM lead_tasks t
            LEFT JOIN places p ON t.place_id = p.place_id
            LEFT JOIN place_status ps ON t.place_id = ps.place_id
            WHERE t.status != 'done'
            ORDER BY t.due_at ASC, t.priority DESC
        `;

        if (status === 'done') {
            query = `
                SELECT t.*, p.name as place_name, p.phone, p.website, ps.status as lead_status 
                FROM lead_tasks t
                LEFT JOIN places p ON t.place_id = p.place_id
                LEFT JOIN place_status ps ON t.place_id = ps.place_id
                WHERE t.status = 'done'
                ORDER BY t.completed_at DESC
                LIMIT ${limit}
            `;
        }

        const tasks = await db.all(query);


        await db.close();
        return NextResponse.json({ success: true, tasks });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function POST(request: Request) {
    const dbPath = path.join(process.cwd(), '../growth/db/growth.db');

    try {
        const body = await request.json();
        const { placeId, dueAt, notes, type, priority, source } = body;

        if (!placeId || !notes) {
            return NextResponse.json({ success: false, error: "placeId and notes required" }, { status: 400 });
        }

        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        // Insert Task
        const res = await db.run(`
            INSERT INTO lead_tasks (place_id, due_at, task_type, status, priority, notes, source, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?)
        `, placeId, dueAt, type || 'follow_up', priority || 'normal', notes, source || 'manual', new Date().toISOString(), new Date().toISOString());

        // Log
        await db.run(`
             INSERT INTO place_activity_log (place_id, action, notes, created_at)
             VALUES (?, 'task_created', ?, ?)
        `, placeId, `Created Task: ${notes}`, new Date().toISOString());



        await db.close();
        return NextResponse.json({ success: true, taskId: res.lastID });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function PUT(request: Request) {
    const dbPath = path.join(process.cwd(), '../growth/db/growth.db');

    try {
        const body = await request.json();
        const { taskId, status } = body;

        if (!taskId || !status) {
            return NextResponse.json({ success: false, error: "taskId and status required" }, { status: 400 });
        }

        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        const now = new Date().toISOString();
        if (status === 'done') {
            await db.run(`
                UPDATE lead_tasks 
                SET status = ?, completed_at = ?, completed_by = 'user', updated_at = ? 
                WHERE task_id = ?
            `, status, now, now, taskId);
        } else {
            await db.run(`
                UPDATE lead_tasks 
                SET status = ?, completed_at = NULL, completed_by = NULL, updated_at = ? 
                WHERE task_id = ?
            `, status, now, taskId);
        }

        await db.close();
        return NextResponse.json({ success: true });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
