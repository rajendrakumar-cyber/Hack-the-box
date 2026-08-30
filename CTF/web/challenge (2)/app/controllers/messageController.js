const { all, get, run } = require('../db');
const { enqueueMessageVisit } = require('../../bot/bot');

async function inbox(req, res, next) {
  try {
    const messages = await all(`
      SELECT
        messages.id,
        messages.from_label,
        messages.created_at,
        users.username AS sender_username
      FROM messages
      JOIN users ON users.id = messages.sender_id
      WHERE messages.recipient_id = ?
      ORDER BY messages.created_at DESC
    `, [req.session.user.id]);

    res.render('inbox', { messages });
  } catch (err) {
    next(err);
  }
}

function newMessage(req, res) {
  res.render('new-message', {
    error: null,
    form: {}
  });
}

async function sendMessage(req, res, next) {
  try {
    const form = {
      to_username: (req.body.to_username || '').trim(),
      content: (req.body.content || '').trim()
    };

    if (!form.to_username || !form.content) {
      res.status(400).render('new-message', {
        error: 'To and content are required.',
        form
      });
      return;
    }

    const recipient = await get(
      'SELECT id, username FROM users WHERE username = ?',
      [form.to_username]
    );

    if (!recipient) {
      res.status(404).render('new-message', {
        error: 'Recipient not found.',
        form
      });
      return;
    }

    const result = await run(`
      INSERT INTO messages (
        sender_id,
        recipient_id,
        from_label,
        content
      )
      VALUES (?, ?, ?, ?)
    `, [
      req.session.user.id,
      recipient.id,
      req.session.user.username,
      form.content
    ]);

    if (recipient.username === 'admin') {
      enqueueMessageVisit(result.lastID);
    }

    res.redirect('/');
  } catch (err) {
    next(err);
  }
}

async function showMessage(req, res, next) {
  try {
    const message = await get(`
      SELECT
        messages.id,
        messages.from_label,
        messages.content,
        messages.created_at,
        users.username AS sender_username
      FROM messages
      JOIN users ON users.id = messages.sender_id
      WHERE messages.id = ?
        AND messages.recipient_id = ?
    `, [req.params.id, req.session.user.id]);

    if (!message) {
      res.status(404).send('Message not found');
      return;
    }

    res.render('message', { message });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  inbox,
  newMessage,
  sendMessage,
  showMessage
};
