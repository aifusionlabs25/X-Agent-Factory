import Database from 'better-sqlite3';
import path from 'path';

// DB Path: ../../intelligence/factory.db (Relative to dashboard root)
// Only initialize once in dev
const dbPath = path.join(process.cwd(), '..', 'intelligence', 'factory.db');

let db: any;

try {
    db = new Database(dbPath, {
        verbose: console.log,
        fileMustExist: true
    });
    db.pragma('journal_mode = WAL');
    console.log('🔌 Connected to Factory DB:', dbPath);
} catch (error) {
    console.error('❌ Failed to connect to Factory DB:', error);
    db = null;
}

export default db;
