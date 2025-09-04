const express = require('express');
const bcrypt = require('bcryptjs');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Get profile
router.get('/', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const userData = user.toJSON();
    
    res.json({
      success: true,
      data: userData
    });
    
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching profile'
    });
  }
});

// Update profile
router.put('/', loginRequired, async (req, res) => {
  try {
    const updates = req.body;
    const user = req.user;
    
    // Only allow specific fields to be updated
    const allowedFields = ['name', 'phone', 'address', 'ownerName'];
    const updateFields = {};
    
    allowedFields.forEach(field => {
      if (updates[field] !== undefined) {
        updateFields[field] = updates[field];
      }
    });
    
    if (Object.keys(updateFields).length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No valid fields to update'
      });
    }
    
    // Update user fields
    Object.assign(user, updateFields);
    await user.save();
    
    const updatedUser = user.toJSON();
    
    res.json({
      success: true,
      data: updatedUser
    });
    
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while updating profile'
    });
  }
});

// Update password
router.put('/password', loginRequired, async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
    const user = req.user;
    
    if (!currentPassword || !newPassword) {
      return res.status(400).json({
        success: false,
        message: 'Current password and new password are required'
      });
    }
    
    if (newPassword.length < 6) {
      return res.status(400).json({
        success: false,
        message: 'New password must be at least 6 characters long'
      });
    }
    
    // Verify current password
    const isCurrentPasswordValid = await user.comparePassword(currentPassword);
    if (!isCurrentPasswordValid) {
      return res.status(401).json({
        success: false,
        message: 'Current password is incorrect'
      });
    }
    
    // Update password
    user.password = newPassword;
    await user.save();
    
    res.json({
      success: true,
      message: 'Password updated successfully'
    });
    
  } catch (error) {
    console.error('Update password error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while updating password'
    });
  }
});

// Delete account
router.delete('/', loginRequired, async (req, res) => {
  try {
    const { password } = req.body;
    const user = req.user;
    
    if (!password) {
      return res.status(400).json({
        success: false,
        message: 'Password is required to delete account'
      });
    }
    
    // Verify password
    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        message: 'Incorrect password'
      });
    }
    
    // Delete user
    await User.findByIdAndDelete(user._id);
    
    res.json({
      success: true,
      message: 'Account deleted successfully'
    });
    
  } catch (error) {
    console.error('Delete account error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while deleting account'
    });
  }
});

module.exports = router;
