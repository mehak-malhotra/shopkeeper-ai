const express = require('express');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Get all customers
router.get('/', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const customers = user.customers || [];
    
    // Remove sensitive data
    const safeCustomers = customers.map(customer => {
      const { password, ...safeCustomer } = customer.toObject ? customer.toObject() : customer;
      return safeCustomer;
    });
    
    res.json({
      success: true,
      data: safeCustomers
    });
    
  } catch (error) {
    console.error('Get customers error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching customers'
    });
  }
});

// Add customer
router.post('/add', loginRequired, async (req, res) => {
  try {
    const { name, phone, address, user_email } = req.body;
    const user = req.user;
    
    if (!phone) {
      return res.status(400).json({
        success: false,
        message: 'Phone number is required'
      });
    }
    
    const customers = user.customers || [];
    
    // Check if customer already exists by phone
    const existingCustomerIndex = customers.findIndex(c => c.phone === phone);
    
    if (existingCustomerIndex !== -1) {
      // Update existing customer
      const existingCustomer = customers[existingCustomerIndex];
      existingCustomer.name = name || existingCustomer.name;
      existingCustomer.address = address || existingCustomer.address;
      existingCustomer.user_email = user_email || user.email;
      
      await user.save();
      
      return res.json({
        success: true,
        data: existingCustomer
      });
    }
    
    // Create new customer
    const customerId = user.getNextCustomerId();
    const newCustomer = {
      customer_id: customerId,
      name: name || '',
      phone: phone,
      address: address || '',
      user_email: user_email || user.email
    };
    
    customers.push(newCustomer);
    await user.save();
    
    res.json({
      success: true,
      data: newCustomer
    });
    
  } catch (error) {
    console.error('Add customer error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while adding customer'
    });
  }
});

// Find customer by phone (used by chatbot)
router.post('/find-by-phone', loginRequired, async (req, res) => {
  try {
    const { phone } = req.body;
    const user = req.user;
    
    if (!phone) {
      return res.status(400).json({
        success: false,
        message: 'Phone number is required'
      });
    }
    
    const customers = user.customers || [];
    const customer = customers.find(c => c.phone === phone);
    
    if (!customer) {
      return res.status(404).json({
        success: false,
        message: 'Customer not found'
      });
    }
    
    res.json({
      success: true,
      data: customer
    });
    
  } catch (error) {
    console.error('Find customer error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while finding customer'
    });
  }
});

// Update customer
router.put('/:customerId', loginRequired, async (req, res) => {
  try {
    const { customerId } = req.params;
    const updates = req.body;
    const user = req.user;
    
    const customers = user.customers || [];
    const customerIndex = customers.findIndex(c => c.customer_id == customerId);
    
    if (customerIndex === -1) {
      return res.status(404).json({
        success: false,
        message: 'Customer not found'
      });
    }
    
    // Update allowed fields
    const allowedFields = ['name', 'phone', 'address', 'user_email'];
    allowedFields.forEach(field => {
      if (updates[field] !== undefined) {
        customers[customerIndex][field] = updates[field];
      }
    });
    
    await user.save();
    
    res.json({
      success: true,
      data: customers[customerIndex]
    });
    
  } catch (error) {
    console.error('Update customer error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while updating customer'
    });
  }
});

// Delete customer
router.delete('/:customerId', loginRequired, async (req, res) => {
  try {
    const { customerId } = req.params;
    const user = req.user;
    
    const customers = user.customers || [];
    const initialLength = customers.length;
    
    user.customers = customers.filter(c => c.customer_id != customerId);
    
    if (user.customers.length === initialLength) {
      return res.status(404).json({
        success: false,
        message: 'Customer not found'
      });
    }
    
    await user.save();
    
    res.json({
      success: true,
      message: 'Customer deleted successfully'
    });
    
  } catch (error) {
    console.error('Delete customer error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while deleting customer'
    });
  }
});

module.exports = router;
