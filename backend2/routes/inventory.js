const express = require('express');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Add inventory item
router.post('/', loginRequired, async (req, res) => {
  try {
    const { name, quantity, price, category, minStock } = req.body;
    const user = req.user;
    
    if (!name || quantity === undefined || price === undefined) {
      return res.status(400).json({
        success: false,
        message: 'Name, quantity, and price are required'
      });
    }
    
    const inventory = user.inventory || [];
    const itemName = name.trim();
    
    // Check if item already exists
    const existingItemIndex = inventory.findIndex(
      item => item.name.toLowerCase() === itemName.toLowerCase()
    );
    
    if (existingItemIndex !== -1) {
      // Update existing item quantity
      inventory[existingItemIndex].quantity += parseInt(quantity);
      await user.save();
      
      return res.json({
        success: true,
        data: inventory[existingItemIndex],
        warning: `Item '${itemName}' already exists. Quantity updated instead of adding a new item.`
      });
    }
    
    // Create new item
    const newItem = {
      name: itemName,
      quantity: parseInt(quantity),
      price: parseFloat(price),
      category: category || 'General',
      minStock: parseInt(minStock) || 5
    };
    
    inventory.push(newItem);
    await user.save();
    
    res.json({
      success: true,
      data: newItem
    });
    
  } catch (error) {
    console.error('Add inventory error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while adding inventory item'
    });
  }
});

// Get all inventory items
router.get('/', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const inventory = user.inventory || [];
    
    res.json({
      success: true,
      data: inventory
    });
    
  } catch (error) {
    console.error('Get inventory error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching inventory'
    });
  }
});

// Update inventory item
router.put('/:itemName', loginRequired, async (req, res) => {
  try {
    const { itemName } = req.params;
    const updates = req.body;
    const user = req.user;
    
    const inventory = user.inventory || [];
    const itemIndex = inventory.findIndex(
      item => item.name.toLowerCase() === itemName.toLowerCase()
    );
    
    if (itemIndex === -1) {
      return res.status(404).json({
        success: false,
        message: 'Item not found'
      });
    }
    
    // Update allowed fields
    const allowedFields = ['name', 'price', 'quantity', 'minStock', 'category'];
    allowedFields.forEach(field => {
      if (updates[field] !== undefined) {
        inventory[itemIndex][field] = updates[field];
      }
    });
    
    await user.save();
    
    res.json({
      success: true,
      data: inventory[itemIndex]
    });
    
  } catch (error) {
    console.error('Update inventory error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while updating inventory item'
    });
  }
});

// Delete inventory item
router.delete('/:itemName', loginRequired, async (req, res) => {
  try {
    const { itemName } = req.params;
    const user = req.user;
    
    const inventory = user.inventory || [];
    const initialLength = inventory.length;
    
    user.inventory = inventory.filter(
      item => item.name.toLowerCase() !== itemName.toLowerCase()
    );
    
    if (user.inventory.length === initialLength) {
      return res.status(404).json({
        success: false,
        message: 'Item not found'
      });
    }
    
    await user.save();
    
    res.json({
      success: true,
      message: 'Item deleted successfully'
    });
    
  } catch (error) {
    console.error('Delete inventory error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while deleting inventory item'
    });
  }
});

// Update inventory quantities (used by chatbot)
router.post('/update-quantities', loginRequired, async (req, res) => {
  try {
    const { updates } = req.body;
    const user = req.user;
    
    if (!Array.isArray(updates)) {
      return res.status(400).json({
        success: false,
        message: 'Updates must be an array'
      });
    }
    
    const inventory = user.inventory || [];
    
    for (const update of updates) {
      const { name, quantity } = update;
      const itemName = name.toLowerCase();
      
      const item = inventory.find(
        invItem => invItem.name.toLowerCase() === itemName
      );
      
      if (!item) {
        return res.status(404).json({
          success: false,
          message: `Item ${name} not found`
        });
      }
      
      const currentQuantity = item.quantity || 0;
      const newQuantity = currentQuantity + quantity;
      
      if (newQuantity < 0) {
        return res.status(400).json({
          success: false,
          message: `Insufficient stock for ${name}`
        });
      }
      
      item.quantity = newQuantity;
    }
    
    await user.save();
    
    res.json({
      success: true,
      message: 'Inventory quantities updated successfully'
    });
    
  } catch (error) {
    console.error('Update quantities error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while updating quantities'
    });
  }
});

module.exports = router;
