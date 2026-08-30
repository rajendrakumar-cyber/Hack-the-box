const bcrypt = require('bcrypt');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const appDir = '/app/app';
const databasePath = path.join(appDir, 'database.sqlite');
const credentialsPath = '/app/admin_credentials.json';
const flagPath = '/flag.txt';

for (const suffix of ['', '-shm', '-wal']) {
  fs.rmSync(`${databasePath}${suffix}`, { force: true });
}

const { close, get, initDb, run } = require(path.join(appDir, 'db'));

function randomPassword() {
  return crypto.randomBytes(24).toString('base64url');
}

async function createUser(username) {
  const password = randomPassword();
  const passwordHash = await bcrypt.hash(password, 10);
  const result = await run(
    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
    [username, passwordHash]
  );

  return {
    id: result.lastID,
    username,
    password
  };
}

async function createMessage(sender, recipient, content) {
  await run(`
    INSERT INTO messages (
      sender_id,
      recipient_id,
      from_label,
      content
    )
    VALUES (?, ?, ?, ?)
  `, [
    sender.id,
    recipient.id,
    sender.username,
    content
  ]);
}

(async () => {
  await initDb();

  const users = {};
  for (const username of ['admin', 'archivist', 'scribe', 'ravenmaster', 'minstrel', 'alchemist']) {
    users[username] = await createUser(username);
  }

  const flag = fs.existsSync(flagPath)
    ? fs.readFileSync(flagPath, 'utf8').trim()
    : 'flag file missing';

  await createMessage(
    users.archivist,
    users.admin,
    `Archive notice:\n\nThe sealed royal record reads:\n${flag}`
  );
  await createMessage(
    users.scribe,
    users.admin,
    'The west tower inventory has been copied into the public ledger.'
  );
  await createMessage(
    users.ravenmaster,
    users.admin,
    'Three ravens returned before sunrise. None carried a reply.'
  );
  await createMessage(
    users.admin,
    users.scribe,
    'Please prepare fresh parchment for the next dispatch.'
  );
  await createMessage(
    users.minstrel,
    users.alchemist,
    'I misplaced the verse about moonlit mercury again.'
  );
  await createMessage(
    users.alchemist,
    users.ravenmaster,
    'The blue vial is stable, but keep it away from open flame.'
  );

  fs.mkdirSync(path.dirname(credentialsPath), { recursive: true });
  fs.writeFileSync(
    credentialsPath,
    JSON.stringify({
      username: users.admin.username,
      password: users.admin.password
    }, null, 2),
    { mode: 0o600 }
  );
  fs.chmodSync(credentialsPath, 0o600);

  const admin = await get('SELECT id, username FROM users WHERE username = ?', ['admin']);
  console.log(`Seeded ${Object.keys(users).length} users and stored admin credentials at ${credentialsPath}`);
  console.log(`Admin user id: ${admin.id}`);
})()
  .catch((err) => {
    console.error('Failed to seed database:', err);
    process.exitCode = 1;
  })
  .finally(async () => {
    await close().catch(() => {});
  });
