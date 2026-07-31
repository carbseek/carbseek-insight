// User accounts in SQLite. Passwords are stored as scrypt hashes ("salt:hash", hex).
const crypto = require('node:crypto');
const db = require('./connection');

function hashPassword(password, salt = crypto.randomBytes(16).toString('hex')) {
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = String(stored || '').split(':');
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(String(password ?? ''), salt, 64);
  const expected = Buffer.from(hash, 'hex');
  return candidate.length === expected.length && crypto.timingSafeEqual(candidate, expected);
}

function findUser(username) {
  return db.prepare('SELECT * FROM users WHERE username = ?').get(username);
}

function createUser(username, password, role = 'admin') {
  db.prepare('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)')
    .run(username, hashPassword(password), role);
  return findUser(username);
}

// Seed the initial admin account when it does not exist yet.
// Initial password comes from ADMIN_INITIAL_PASSWORD, defaulting to "admin123".
function ensureAdminSeed() {
  const username = process.env.ADMIN_USERNAME || 'admin';
  if (findUser(username)) return false;
  createUser(username, process.env.ADMIN_INITIAL_PASSWORD || 'admin123');
  return true;
}

module.exports = { hashPassword, verifyPassword, findUser, createUser, ensureAdminSeed };
