const fs = require('fs/promises');
const { firefox } = require('playwright');

const APP_URL = 'http://127.0.0.10:3000';
const CREDENTIALS_FILE = '/app/admin_credentials.json';
const VISIT_TIMEOUT_MS = 10000;
const WAIT_AFTER_LOAD_MS = 2000;

let queue = Promise.resolve();

function appUrl(pathname) {
  return new URL(pathname, APP_URL).toString();
}

async function readAdminCredentials() {
  const raw = await fs.readFile(CREDENTIALS_FILE, 'utf8');
  const credentials = JSON.parse(raw);

  if (!credentials.username || !credentials.password) {
    throw new Error(`Admin credentials file is missing username or password: ${CREDENTIALS_FILE}`);
  }

  return credentials;
}

async function loginAsAdmin(page) {
  const { username, password } = await readAdminCredentials();

  await page.goto(appUrl('/login'), {
    waitUntil: 'domcontentloaded',
    timeout: VISIT_TIMEOUT_MS
  });
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);

  await Promise.all([
    page.waitForURL(appUrl('/'), { timeout: VISIT_TIMEOUT_MS }),
    page.click('button[type="submit"]')
  ]);
}

async function visitMessage(messageId) {
  const browser = await firefox.launch({
    headless: true
  });
  const context = await browser.newContext();

  try {
    const page = await context.newPage();
    const targetUrl = appUrl(`/messages/${encodeURIComponent(messageId)}`);

    await loginAsAdmin(page);
    console.log(`Admin bot visiting ${targetUrl}`);
    await page.goto(targetUrl, {
      waitUntil: 'load',
      timeout: VISIT_TIMEOUT_MS
    });
    await page.waitForTimeout(WAIT_AFTER_LOAD_MS);
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

function enqueueMessageVisit(messageId) {
  const task = queue
    .catch(() => {})
    .then(() => visitMessage(messageId));

  queue = task.catch((err) => {
    console.error('Admin bot failed:', err);
  });

  return queue;
}

module.exports = {
  enqueueMessageVisit,
  visitMessage
};
