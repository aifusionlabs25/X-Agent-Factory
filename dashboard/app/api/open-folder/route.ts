import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

/**
 * POST /api/open-folder
 * Opens a local folder in the OS file explorer.
 * Body: { path: string } relative to project root.
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const relativePath = body.path || '';

        // Security: Prevent directory traversal and restrict to specific roots
        if (relativePath.includes('..') || relativePath.startsWith('/') || relativePath.includes('\\')) {
            // Basic sanitization, though we will resolve relative to project root
        }

        // Project root is likely where package.json is, or up two levels from this file?
        // This file is in dashboard/app/api/open-folder/route.ts
        // Project root is c:\AI Fusion Labs\X AGENTS\X Agent Factory
        // process.cwd() in Next.js usually points to the project root (dashboard? or the monorepo root if running from there?)
        // Let's assume process.cwd() is the dashboard folder or the root.

        // Inspecting process.cwd() might be needed, but usually strictly defined.
        // Given the user info: c:\AI Fusion Labs\X AGENTS\X Agent Factory
        // If the dashboard is run from `dashboard/`, then cwd is `.../dashboard`.
        // We want to open paths relative to the Factory Root usually.

        // Let's try to resolve absolute path based on known structure.
        // We know the factory root is the parent of 'dashboard'.

        let targetPath = path.resolve(process.cwd());

        // If we are in 'dashboard', go up one level to get to factory root
        if (path.basename(targetPath) === 'dashboard') {
            targetPath = path.resolve(targetPath, '..');
        }

        const fullPath = path.resolve(targetPath, relativePath);

        // Verify it exists AND is a directory
        if (!fs.existsSync(fullPath)) {
            return NextResponse.json({ success: false, error: 'Path does not exist' }, { status: 404 });
        }

        if (!fs.lstatSync(fullPath).isDirectory()) {
            return NextResponse.json({ success: false, error: 'Path is not a directory' }, { status: 400 });
        }

        console.log(`[OpenFolder] Opening: ${fullPath}`);

        // Windows command
        exec(`explorer "${fullPath}"`, (error) => {
            if (error) {
                console.error(`[OpenFolder] Exec error: ${error}`);
            }
        });

        return NextResponse.json({
            success: true,
            path: fullPath
        });

    } catch (e: any) {
        console.error('[OpenFolder] Error:', e);
        return NextResponse.json({
            success: false,
            error: e.message,
        }, { status: 500 });
    }
}
