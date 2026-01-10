import { NextResponse } from 'next/server';
import db from '@/lib/db';

export async function GET(request: Request) {
    try {
        if (!db) {
            return NextResponse.json(
                { error: 'Database connection failed' },
                { status: 500 }
            );
        }

        const { searchParams } = new URL(request.url);
        const vertical = searchParams.get('vertical');
        const limit = searchParams.get('limit') || 100;

        let query = 'SELECT * FROM leads';
        const params = [];

        if (vertical) {
            query += ' WHERE vertical LIKE ?';
            params.push(`%${vertical}%`);
        }

        query += ' ORDER BY created_at DESC LIMIT ?';
        params.push(limit);

        const stmt = db.prepare(query);
        const leads = stmt.all(...params);

        return NextResponse.json({ leads });
    } catch (error: any) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: error.message || 'Internal Server Error' },
            { status: 500 }
        );
    }
}

export async function DELETE(request: Request) {
    try {
        if (!db) {
            return NextResponse.json({ error: 'Database connection failed' }, { status: 500 });
        }

        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id');

        if (!id) {
            return NextResponse.json({ error: 'Missing ID' }, { status: 400 });
        }

        const stmt = db.prepare('DELETE FROM leads WHERE id = ?');
        const result = stmt.run(id);

        return NextResponse.json({ success: true, changes: result.changes });

    } catch (error: any) {
        return NextResponse.json(
            { error: error.message || 'Internal Server Error' },
            { status: 500 }
        );
    }
}

// Update Status (or other fields)
export async function POST(request: Request) {
    try {
        if (!db) {
            return NextResponse.json({ error: 'Database connection failed' }, { status: 500 });
        }

        const body = await request.json();
        const { id, status, notes } = body;

        if (!id) {
            return NextResponse.json({ error: 'Missing ID' }, { status: 400 });
        }

        if (status) {
            const stmt = db.prepare('UPDATE leads SET status = ? WHERE id = ?');
            stmt.run(status, id);
        }

        // Placeholder for notes update if schema supported it
        // if (notes) ...

        return NextResponse.json({ success: true });

    } catch (error: any) {
        return NextResponse.json(
            { error: error.message || 'Internal Server Error' },
            { status: 500 }
        );
    }
}
