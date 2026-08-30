import { Elysia } from 'elysia'
import { Database } from 'bun:sqlite'
import bcrypt from 'bcryptjs'
import { randomBytes } from 'node:crypto'

const db = new Database('game.db')
const adminPassword = randomBytes(24).toString('base64url')
const adminPasswordHash = await bcrypt.hash(adminPassword, 12)
const sessionSecret = randomBytes(32).toString('hex')
const sessionMaxAge = 60 * 60
const sessionCookie = 'session'
const flag = (await Bun.file('/flag.txt').text()).trim()

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
  );
`)

db.query(
  `INSERT INTO users (username, password_hash, role)
   VALUES (?, ?, ?)
   ON CONFLICT(username) DO UPDATE SET
     password_hash = excluded.password_hash,
     role = excluded.role`
).run('admin', adminPasswordHash, 'admin')

const findUser = db.query<
  { id: number; username: string; role: string; password_hash: string },
  [string]
>('SELECT id, username, role, password_hash FROM users WHERE username = ?')

function setSessionCookie(session: { set: (config: Record<string, unknown>) => void }, value: string) {
  session.set({
    value,
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: sessionMaxAge
  })
}

const app = new Elysia({
  cookie: {
    secrets: [sessionSecret],
    sign: [sessionCookie]
  }
})
  .get('/api/me', ({ cookie: { session }, set }) => {
    if (session.value !== 'admin' && session.value !== 'inside') {
      set.status = 401
      return { authenticated: false }
    }

    return {
      authenticated: true,
      user: {
        username: 'admin',
        role: 'admin'
      },
      gateOpen: true,
      insideGate: session.value === 'inside'
    }
  })
  .post('/api/login', async ({ body, cookie: { session }, set }) => {
    const credentials = body as { username?: string; password?: string }
    const user = credentials.username ? findUser.get(credentials.username) : null
    const passwordMatches =
      Boolean(credentials.password && user) &&
      await bcrypt.compare(credentials.password!, user!.password_hash)

    if (!user || !passwordMatches || user.role !== 'admin') {
      set.status = 401
      return { ok: false, message: 'Invalid credentials' }
    }

    setSessionCookie(session, 'admin')

    return {
      ok: true,
      role: user.role,
      gateOpen: true,
      insideGate: false
    }
  })
  .post('/api/logout', ({ cookie: { session } }) => {
    session.remove()

    return { ok: true }
  })
  .post('/api/gate/open', ({ cookie: { session }, set }) => {
    if (session.value !== 'admin' && session.value !== 'inside') {
      set.status = 403
      return { ok: false, gateOpen: false }
    }

    return { ok: true, gateOpen: true, insideGate: false }
  })
  .post('/api/gate/enter', ({ cookie: { session }, set }) => {
    if (!session.value) {
      set.status = 401
      return { ok: false, message: 'Login required' }
    }

    if (session.value !== 'admin' && session.value !== 'inside') {
      set.status = 403
      return { ok: false, message: 'Gate authority required' }
    }

    setSessionCookie(session, 'inside')

    return { ok: true, insideGate: true }
  })
  .post('/api/flag', ({ cookie: { session }, set }) => {
    if (!session.value) {
      set.status = 401
      return { ok: false, message: 'Login required' }
    }

    if (session.value !== 'inside') {
      set.status = 403
      return { ok: false, message: 'Enter the castle first' }
    }

    return { ok: true, flag }
  })

app.listen(3000)
