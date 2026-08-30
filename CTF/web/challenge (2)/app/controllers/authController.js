const bcrypt = require('bcrypt');

const { get, run } = require('../db');

function renderRegister(res, error = null) {
  res.render('register', { error });
}

function renderLogin(res, error = null) {
  res.render('login', { error });
}

async function register(req, res, next) {
  try {
    const username = (req.body.username || '').trim();
    const password = req.body.password || '';

    if (!username || !password) {
      renderRegister(res.status(400), 'Username and password are required.');
      return;
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const result = await run(
      'INSERT INTO users (username, password_hash) VALUES (?, ?)',
      [username, passwordHash]
    );

    req.session.user = {
      id: result.lastID,
      username
    };

    res.redirect('/');
  } catch (err) {
    if (err.code === 'SQLITE_CONSTRAINT') {
      renderRegister(res.status(409), 'Username already exists.');
      return;
    }

    next(err);
  }
}

async function login(req, res, next) {
  try {
    const username = (req.body.username || '').trim();
    const password = req.body.password || '';

    if (!username || !password) {
      renderLogin(res.status(400), 'Username and password are required.');
      return;
    }

    const user = await get(
      'SELECT id, username, password_hash FROM users WHERE username = ?',
      [username]
    );

    if (!user || !(await bcrypt.compare(password, user.password_hash))) {
      renderLogin(res.status(401), 'Invalid username or password.');
      return;
    }

    req.session.user = {
      id: user.id,
      username: user.username
    };

    res.redirect('/');
  } catch (err) {
    next(err);
  }
}

function logout(req, res, next) {
  req.session.destroy((err) => {
    if (err) {
      next(err);
      return;
    }

    res.redirect('/login');
  });
}

module.exports = {
  login,
  logout,
  register,
  showLogin: (req, res) => renderLogin(res),
  showRegister: (req, res) => renderRegister(res)
};
