const express = require('express');

const authController = require('./controllers/authController');
const messageController = require('./controllers/messageController');
const { requireAuth } = require('./middleware/auth');

const router = express.Router();

// Messages routes

router.get('/', requireAuth, messageController.inbox);
router.get('/messages/new', requireAuth, messageController.newMessage);
router.post('/messages', requireAuth, messageController.sendMessage);
router.get('/messages/:id', requireAuth, messageController.showMessage);

// Auth routes

router.get('/register', authController.showRegister);
router.post('/register', authController.register);
router.get('/login', authController.showLogin);
router.post('/login', authController.login);
router.post('/logout', authController.logout);

module.exports = router;



