import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

// Configuration
const FACTORY_ROOT = path.resolve(process.cwd(), '../');
const SCENARIOS_DIR = path.join(FACTORY_ROOT, 'tools', 'evaluation', 'dojo', 'scenarios');

function getScenarios(dir: string, relativePath = ''): any[] {
    let results: any[] = [];
    const list = fs.readdirSync(dir);

    for (const file of list) {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);

        if (stat && stat.isDirectory()) {
            results = results.concat(getScenarios(filePath, path.join(relativePath, file)));
        } else if (file.endsWith('.json')) {
            // Read metadata?
            // For speed, just use filename.
            // Or optional read.
            results.push({
                id: path.join('tools', 'evaluation', 'dojo', 'scenarios', relativePath, file).replace(/\\/g, '/'),
                path: path.join(relativePath, file).replace(/\\/g, '/'),
                name: file.replace('.json', ''),
                group: relativePath.replace(/\\/g, '/') || 'Root'
            });
        }
    }
    return results;
}

export async function GET() {
    try {
        if (!fs.existsSync(SCENARIOS_DIR)) {
            return NextResponse.json({ scenarios: [] });
        }

        const scenarios = getScenarios(SCENARIOS_DIR);
        return NextResponse.json({ scenarios });
    } catch (e) {
        return NextResponse.json({ error: 'Failed to list scenarios' }, { status: 500 });
    }
}
