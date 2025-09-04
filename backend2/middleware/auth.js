const jwt = require('jsonwebtoken');
const User = require('../models/User');

// Simple token storage (in production, use Redis or database)
const tokenStore = new Map();

const generateToken = (userEmail) => {
  const token = jwt.sign(
    { email: userEmail },
    process.env.JWT_SECRET,
    { expiresIn: '24h' }
  );
  
  // Store token in memory (for logout functionality)
  tokenStore.set(token, { email: userEmail, createdAt: Date.now() });
  
  return token;
};

const decodeToken = (token) => {
  try {
    // Check if token exists in store
    if (!tokenStore.has(token)) {
      return null;
    }
    
    // Verify JWT token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (error) {
    return null;
  }
};

const loginRequired = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'Missing or invalid token'
      });
    }
    
    const token = authHeader.split(' ')[1];
    const payload = decodeToken(token);
    
    if (!payload || !payload.email) {
      return res.status(401).json({
        success: false,
        message: 'Invalid token'
      });
    }
    
    // Verify user still exists
    const user = await User.findOne({ email: payload.email });
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'User not found'
      });
    }
    
    req.user = user;
    req.userEmail = payload.email;
    next();
  } catch (error) {
    return res.status(401).json({
      success: false,
      message: 'Authentication failed'
    });
  }
};

const logout = (token) => {
  tokenStore.delete(token);
};

// Clean up expired tokens periodically
setInterval(() => {
  const now = Date.now();
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours
  
  for (const [token, data] of tokenStore.entries()) {
    if (now - data.createdAt > maxAge) {
      tokenStore.delete(token);
    }
  }
}, 60 * 60 * 1000); // Clean up every hour

module.exports = {
  generateToken,
  decodeToken,
  loginRequired,
  logout
};
