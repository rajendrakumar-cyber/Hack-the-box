function requireAuth(req, res, next) {
  if (!req.session.user) {
    res.redirect('/login');
    return;
  }

  next();
}

module.exports = {
  requireAuth
};
