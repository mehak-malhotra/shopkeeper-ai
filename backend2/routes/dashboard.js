const express = require('express');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Get dashboard statistics
router.get('/stats', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const orders = user.orders || [];
    const inventory = user.inventory || [];
    
    // Calculate statistics
    const totalOrders = orders.length;
    const pendingOrders = orders.filter(order => order.status === 'pending').length;
    const totalRevenue = orders.reduce((sum, order) => sum + (order.total || 0), 0);
    const totalProducts = inventory.length;
    const lowStockItems = inventory.filter(item => 
      (item.quantity || 0) <= (item.minStock || 0)
    ).length;
    
    // Calculate recent orders (last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const recentOrders = orders.filter(order => {
      const orderDate = new Date(order.timestamp);
      return orderDate >= thirtyDaysAgo;
    });
    
    const recentRevenue = recentOrders.reduce((sum, order) => sum + (order.total || 0), 0);
    
    // Calculate top selling items
    const itemSales = {};
    orders.forEach(order => {
      if (order.items && Array.isArray(order.items)) {
        order.items.forEach(item => {
          const itemName = item.name;
          if (!itemSales[itemName]) {
            itemSales[itemName] = {
              name: itemName,
              totalQuantity: 0,
              totalRevenue: 0
            };
          }
          itemSales[itemName].totalQuantity += item.quantity || 0;
          itemSales[itemName].totalRevenue += item.total || 0;
        });
      }
    });
    
    const topSellingItems = Object.values(itemSales)
      .sort((a, b) => b.totalQuantity - a.totalQuantity)
      .slice(0, 5);
    
    // Calculate order status distribution
    const statusDistribution = {};
    orders.forEach(order => {
      const status = order.status || 'unknown';
      statusDistribution[status] = (statusDistribution[status] || 0) + 1;
    });
    
    // Calculate monthly revenue (last 6 months)
    const monthlyRevenue = {};
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    
    orders.forEach(order => {
      const orderDate = new Date(order.timestamp);
      if (orderDate >= sixMonthsAgo) {
        const monthKey = `${orderDate.getFullYear()}-${String(orderDate.getMonth() + 1).padStart(2, '0')}`;
        monthlyRevenue[monthKey] = (monthlyRevenue[monthKey] || 0) + (order.total || 0);
      }
    });
    
    const stats = {
      totalOrders,
      pendingOrders,
      lowStockItems,
      totalRevenue,
      totalProducts,
      recentRevenue,
      topSellingItems,
      statusDistribution,
      monthlyRevenue,
      averageOrderValue: totalOrders > 0 ? totalRevenue / totalOrders : 0,
      completionRate: totalOrders > 0 ? ((totalOrders - pendingOrders) / totalOrders) * 100 : 0
    };
    
    res.json({
      success: true,
      data: stats
    });
    
  } catch (error) {
    console.error('Dashboard stats error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching dashboard statistics'
    });
  }
});

// Get recent activity
router.get('/activity', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const orders = user.orders || [];
    
    // Get recent orders (last 10)
    const recentOrders = orders
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 10)
      .map(order => ({
        id: order.order_id,
        type: 'order',
        description: `Order #${order.order_id} - ${order.customer_name || 'Unknown Customer'}`,
        amount: order.total,
        status: order.status,
        timestamp: order.timestamp,
        items: order.items?.length || 0
      }));
    
    res.json({
      success: true,
      data: recentOrders
    });
    
  } catch (error) {
    console.error('Dashboard activity error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching recent activity'
    });
  }
});

// Get inventory alerts
router.get('/alerts', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    const inventory = user.inventory || [];
    
    // Low stock alerts
    const lowStockAlerts = inventory
      .filter(item => (item.quantity || 0) <= (item.minStock || 0))
      .map(item => ({
        type: 'low_stock',
        severity: 'warning',
        message: `${item.name} is running low (${item.quantity} remaining)`,
        itemName: item.name,
        currentStock: item.quantity,
        minStock: item.minStock
      }));
    
    // Out of stock alerts
    const outOfStockAlerts = inventory
      .filter(item => (item.quantity || 0) === 0)
      .map(item => ({
        type: 'out_of_stock',
        severity: 'error',
        message: `${item.name} is out of stock`,
        itemName: item.name,
        currentStock: item.quantity
      }));
    
    const alerts = [...lowStockAlerts, ...outOfStockAlerts];
    
    res.json({
      success: true,
      data: alerts
    });
    
  } catch (error) {
    console.error('Dashboard alerts error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching alerts'
    });
  }
});

module.exports = router;
