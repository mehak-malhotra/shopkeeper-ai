const express = require('express');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Create order
router.post('/', loginRequired, async (req, res) => {
  try {
    const {
      customerPhone,
      customerName,
      address,
      items,
      total,
      status,
      timestamp,
      notes
    } = req.body;
    
    const user = req.user;
    const customers = user.customers || [];
    const orders = user.orders || [];
    
    // Find customer by phone
    let customerId = null;
    let existingCustomer = customers.find(c => c.phone === customerPhone);
    
    if (existingCustomer) {
      customerId = existingCustomer.customer_id;
    } else if (customerPhone) {
      // Create new customer
      customerId = user.getNextCustomerId();
      const newCustomer = {
        customer_id: customerId,
        name: customerName || 'Unknown Customer',
        phone: customerPhone,
        address: address || '',
        user_email: user.email
      };
      customers.push(newCustomer);
    }
    
    // Create order
    const orderId = user.getNextOrderId();
    const order = {
      order_id: orderId,
      customer_id: customerId,
      customer_phone: customerPhone,
      customer_name: customerName,
      items: items || [],
      total: total || 0,
      status: status || 'pending',
      timestamp: timestamp || new Date().toISOString(),
      notes: notes || ''
    };
    
    orders.push(order);
    user.customers = customers;
    user.orders = orders;
    await user.save();
    
    res.json({
      success: true,
      data: order,
      message: `Order placed successfully! Your order ID is ${orderId}.`
    });
    
  } catch (error) {
    console.error('Create order error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while creating order'
    });
  }
});

// Create direct order (compatible with new logic)
router.post('/direct', loginRequired, async (req, res) => {
  try {
    const { customer, order: orderData } = req.body;
    const user = req.user;
    
    const customers = user.customers || [];
    const orders = user.orders || [];
    
    // Handle customer
    const customerPhone = customer.phone || '';
    const customerName = customer.name || '';
    const customerAddress = customer.address || '';
    const customerEmail = customer.user_email || user.email;
    
    // Find or create customer
    let customerId = null;
    let existingCustomer = customers.find(c => c.phone === customerPhone);
    
    if (existingCustomer) {
      customerId = existingCustomer.customer_id;
      // Update customer info if needed
      existingCustomer.name = customerName || existingCustomer.name;
      existingCustomer.address = customerAddress || existingCustomer.address;
      existingCustomer.user_email = customerEmail;
    } else if (customerPhone) {
      customerId = user.getNextCustomerId();
      const newCustomer = {
        customer_id: customerId,
        name: customerName,
        phone: customerPhone,
        address: customerAddress,
        user_email: customerEmail
      };
      customers.push(newCustomer);
    }
    
    // Create order
    const orderId = user.getNextOrderId();
    const order = {
      order_id: orderId,
      customer_id: customerId,
      customer_phone: customerPhone,
      customer_name: customerName,
      items: orderData.items || [],
      total: orderData.total || 0,
      status: 'pending',
      timestamp: new Date().toISOString(),
      notes: orderData.notes || ''
    };
    
    orders.push(order);
    user.customers = customers;
    user.orders = orders;
    await user.save();
    
    res.json({
      success: true,
      data: {
        order_id: orderId,
        customer_id: customerId,
        total: order.total
      },
      message: `Order placed successfully! Order ID: ${orderId}, Customer ID: ${customerId}`
    });
    
  } catch (error) {
    console.error('Create direct order error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while creating direct order'
    });
  }
});

// Get all orders
router.get('/', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const orders = user.orders || [];
    
    res.json({
      success: true,
      data: orders
    });
    
  } catch (error) {
    console.error('Get orders error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching orders'
    });
  }
});

// Get specific order
router.get('/:orderId', loginRequired, async (req, res) => {
  try {
    const { orderId } = req.params;
    const user = req.user;
    const orders = user.orders || [];
    
    const order = orders.find(o => o.order_id == orderId);
    
    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }
    
    res.json({
      success: true,
      data: order
    });
    
  } catch (error) {
    console.error('Get order error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching order'
    });
  }
});

// Update order
router.put('/:orderId', loginRequired, async (req, res) => {
  try {
    const { orderId } = req.params;
    const updates = req.body;
    const user = req.user;
    
    const orders = user.orders || [];
    const orderIndex = orders.findIndex(o => o.order_id == orderId);
    
    if (orderIndex === -1) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }
    
    // Update allowed fields
    const allowedFields = ['items', 'total', 'status', 'timestamp', 'notes'];
    allowedFields.forEach(field => {
      if (updates[field] !== undefined) {
        orders[orderIndex][field] = updates[field];
      }
    });
    
    await user.save();
    
    res.json({
      success: true,
      data: orders[orderIndex]
    });
    
  } catch (error) {
    console.error('Update order error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while updating order'
    });
  }
});

// Delete order
router.delete('/:orderId', loginRequired, async (req, res) => {
  try {
    const { orderId } = req.params;
    const user = req.user;
    
    const orders = user.orders || [];
    const initialLength = orders.length;
    
    user.orders = orders.filter(o => o.order_id != orderId);
    
    if (user.orders.length === initialLength) {
      return res.status(404).json({
        success: false,
        message: 'Order not found'
      });
    }
    
    await user.save();
    
    res.json({
      success: true,
      message: 'Order deleted successfully'
    });
    
  } catch (error) {
    console.error('Delete order error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while deleting order'
    });
  }
});

module.exports = router;
