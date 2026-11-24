import express from 'express';
import cors from 'cors';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { scoreAssessment, detectRisk, crisisReply } from './scoring.js';
import { answerWithKnowledge, modelStatus } from './assistant.js';
import { parsePilotFiles, calculatePilotDecision } from './pilot.js';
import { topicCatalog } from './qa-bank.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataFile = path.join(here, 'data', 'mindmate.json');
const secret = process.env.JWT_SECRET || 'local-development-secret-change-me';
const port = Number(process.env.PORT || 8080);
function pilotSeed() {
  const results = path.resolve(here, '..', '..', 'pilot', 'real-results', 'current-comparison');
  const logs = path.resolve(here, '..', '..', 'pilot', 'real-results');
  try {
    return parsePilotFiles({
      autoScoresCsv: fs.readFileSync(path.join(results, 'comparison_summary.csv'), 'utf8'),
      escalationDetailCsv: fs.readFileSync(path.join(results, 'escalation_detail.csv'), 'utf8'),
      trainLogs: ['qwen35_4b', 'llama32_3b'].map(model =>
        JSON.parse(fs.readFileSync(path.join(logs, model, `train_log_${model}.json`), 'utf8')))
    });
  } catch { return {}; }
}
const initial = { users: [], assessments: [], chats: [], resources: [
  { id: 1, title: '60-second grounding', category: 'Anxiety', body: 'Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 you taste.' },
  { id: 2, title: 'Exam-pressure reset', category: 'Academic stress', body: 'Choose one 20-minute task, silence notifications, then take a 5-minute break.' },
  { id: 3, title: 'Sleep wind-down', category: 'Sleep', body: 'Keep a consistent wake time and move bright screens away for the final 30 minutes.' }
], pilotResults: pilotSeed() };
const pilot = {
  version: 'v1',
  trainConversations: 50,
  trainingRecords: 150,
  testConversations: 20,
  testPrompts: 288,
  keyPrompts: 120,
  languages: ['Banglish', 'English', 'Bangla'],
  models: [
    { key: 'gemma4_e4b', name: 'Gemma 4 E4B', status: 'Pending GPU run' },
    { key: 'qwen35_4b', name: 'Qwen3.5 4B', status: 'Pending GPU run' },
    { key: 'llama32_3b', name: 'Llama 3.2 3B', status: 'Pending GPU run' }
  ],
  safetyGate: { escalationRecall: 90, safeRatings: 95 },
  conditions: ['A_base', 'B_prompt', 'C_finetuned']
};
function readDb() { try { return JSON.parse(fs.readFileSync(dataFile, 'utf8')); } catch { return structuredClone(initial); } }
function writeDb(db) { fs.mkdirSync(path.dirname(dataFile), { recursive: true }); fs.writeFileSync(dataFile, JSON.stringify(db, null, 2)); }
let db = readDb();
async function seed() {
  if (!db.users.length) {
    db.users.push({ id: 'student-demo', name: 'Demo Student', email: 'student@mindmate.local', password: await bcrypt.hash('Student123!', 10), role: 'student', consent: true },
      { id: 'admin-demo', name: 'Research Admin', email: 'admin@mindmate.local', password: await bcrypt.hash('Admin123!', 10), role: 'admin', consent: true });
    writeDb(db);
  }
}
await seed();
const app = express();
app.use(cors({ origin: process.env.CLIENT_ORIGIN || true }));
app.use(express.json({ limit: '6mb' }));
const publicUser = u => ({ id: u.id, name: u.name, email: u.email, role: u.role });
const tokenFor = u => jwt.sign({ id: u.id, role: u.role }, secret, { expiresIn: '8h' });
function auth(req, res, next) { try { req.auth = jwt.verify((req.headers.authorization || '').replace('Bearer ', ''), secret); next(); } catch { res.status(401).json({ error: 'Please sign in again.' }); } }

app.get('/api/health', async (_req, res) => res.json({ ok: true, mode: 'research-prototype', assistant: await modelStatus() }));
app.post('/api/auth/register', async (req, res) => {
  const { name, email, password, consent } = req.body;
  if (!name || !email || !password || !consent) return res.status(400).json({ error: 'Name, email, password, and consent are required.' });
  if (password.length < 8) return res.status(400).json({ error: 'Use at least 8 characters.' });
  if (db.users.some(u => u.email.toLowerCase() === email.toLowerCase())) return res.status(409).json({ error: 'Email is already registered.' });
  const user = { id: crypto.randomUUID(), name, email: email.toLowerCase(), password: await bcrypt.hash(password, 10), role: 'student', consent: true };
  db.users.push(user); writeDb(db); res.status(201).json({ token: tokenFor(user), user: publicUser(user) });
});
app.post('/api/auth/login', async (req, res) => {
  const user = db.users.find(u => u.email.toLowerCase() === String(req.body.email).toLowerCase());
  if (!user || !(await bcrypt.compare(req.body.password || '', user.password))) return res.status(401).json({ error: 'Invalid email or password.' });
  res.json({ token: tokenFor(user), user: publicUser(user) });
});
app.get('/api/me', auth, (req, res) => res.json(publicUser(db.users.find(u => u.id === req.auth.id))));
app.get('/api/resources', (_req, res) => res.json(db.resources));
app.get('/api/topics', (_req, res) => res.json(topicCatalog));
app.post('/api/assessments', auth, (req, res) => {
  const validScale = (value, length, max) => Array.isArray(value) && value.length === length && value.every(n => Number.isInteger(n) && n >= 0 && n <= max);
  if (!validScale(req.body.phq, 9, 3) || !validScale(req.body.gad, 7, 3) || !validScale(req.body.pss, 4, 4)) {
    return res.status(400).json({ error: 'Please answer every screening question before viewing your summary.' });
  }
  const result = scoreAssessment(req.body);
  const record = { id: crypto.randomUUID(), userId: req.auth.id, createdAt: new Date().toISOString(), answers: req.body, result };
  db.assessments.push(record); writeDb(db); res.status(201).json(record);
});
app.get('/api/assessments', auth, (req, res) => res.json(db.assessments.filter(a => a.userId === req.auth.id).map(({ answers, ...safe }) => safe).reverse()));
app.post('/api/chat', auth, async (req, res) => {
  const message = String(req.body.message || '').slice(0, 1500);
  if (!message.trim()) return res.status(400).json({ error: 'Message is required.' });
  const risk = detectRisk(message);
  let response;
  if (risk.level === 'crisis') response = { reply: crisisReply(message), sources: [], engine: 'safety-layer', model: null };
  else response = await answerWithKnowledge({ message, history: Array.isArray(req.body.history) ? req.body.history : [] });
  const entry = { id: crypto.randomUUID(), userId: req.auth.id, createdAt: new Date().toISOString(), message, ...response, risk };
  db.chats.push(entry); writeDb(db); res.json(entry);
});
app.get('/api/admin/summary', auth, (req, res) => {
  if (req.auth.role !== 'admin') return res.status(403).json({ error: 'Admin access required.' });
  const counts = { lower: 0, elevated: 0, higher: 0 };
  db.assessments.forEach(a => counts[a.result.concern.split(' ')[0].toLowerCase()]++);
  res.json({ students: db.users.filter(u => u.role === 'student').length, assessments: db.assessments.length, chats: db.chats.length, crisisFlags: db.chats.filter(c => c.risk.level === 'crisis').length, concernDistribution: counts, pilot: { ...pilot, decision: calculatePilotDecision(db.pilotResults) } });
});
app.post('/api/admin/pilot-results', auth, (req, res) => {
  if (req.auth.role !== 'admin') return res.status(403).json({ error: 'Admin access required.' });
  try {
    db.pilotResults = parsePilotFiles(req.body, db.pilotResults);
    writeDb(db);
    res.json(calculatePilotDecision(db.pilotResults));
  } catch (error) { res.status(400).json({ error: error.message }); }
});
const dist = path.resolve(here, '..', 'dist');
if (fs.existsSync(dist)) { app.use(express.static(dist)); app.use((_req, res) => res.sendFile(path.join(dist, 'index.html'))); }
app.listen(port, () => console.log(`MindMate API running at http://localhost:${port}`));
