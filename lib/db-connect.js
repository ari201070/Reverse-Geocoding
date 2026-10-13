import sqlite3 from 'sqlite3';
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DB_PATH = path.resolve(__dirname, '../data/photo_catalog.db');

export function obtenerConexion() {
  return new Promise((resolve, reject) => {
    const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READWRITE, (err) => {
      if (err) {
        console.error('❌ Error crítico de apertura en photo_catalog.db:', err.message);
        return reject(err);
      }
    });

    db.configure('busyTimeout', 5000);

    db.run('PRAGMA foreign_keys = ON;', (pragmaErr) => {
      if (pragmaErr) {
        console.error('❌ Error al activar PRAGMA foreign_keys:', pragmaErr.message);
        db.close();
        return reject(pragmaErr);
      }
      resolve(db);
    });
  });
}
