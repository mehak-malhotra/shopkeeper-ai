const axios = require('axios');

// Test configuration
const BASE_URL = 'http://localhost:5000';
const TEST_USER = {
  email: 'test@shopkeeper.com',
  password: 'testpassword123',
  name: 'Test Shop',
  phone: '+1234567890',
  ownerName: 'John Doe',
  address: '123 Test Street, Test City'
};

async function testHealthCheck() {
  try {
    console.log('🔍 Testing health check...');
    const response = await axios.get(`${BASE_URL}/health`);
    console.log('✅ Health check passed:', response.data);
    return true;
  } catch (error) {
    console.log('❌ Health check failed:', error.message);
    return false;
  }
}

async function testUserRegistration() {
  try {
    console.log('🔍 Testing user registration...');
    const response = await axios.post(`${BASE_URL}/api/auth/register`, TEST_USER);
    console.log('✅ User registration successful:', response.data);
    return true;
  } catch (error) {
    if (error.response?.status === 400 && error.response?.data?.message?.includes('already registered')) {
      console.log('✅ User already exists (expected):', error.response.data.message);
      return true;
    }
    console.log('❌ User registration failed:', error.response?.data || error.message);
    return false;
  }
}

async function testUserLogin() {
  try {
    console.log('🔍 Testing user login...');
    const response = await axios.post(`${BASE_URL}/api/auth/login`, {
      email: TEST_USER.email,
      password: TEST_USER.password
    });
    console.log('✅ User login successful');
    return response.data.token;
  } catch (error) {
    console.log('❌ User login failed:', error.response?.data || error.message);
    return null;
  }
}

async function testInventoryAPI(token) {
  try {
    console.log('🔍 Testing inventory API...');
    const headers = { Authorization: `Bearer ${token}` };
    
    // Test getting inventory
    const getResponse = await axios.get(`${BASE_URL}/api/inventory`, { headers });
    console.log('✅ Get inventory successful:', getResponse.data);
    
    // Test adding inventory item
    const addResponse = await axios.post(`${BASE_URL}/api/inventory`, {
      name: 'Test Item',
      quantity: 10,
      price: 5.99,
      category: 'Test Category'
    }, { headers });
    console.log('✅ Add inventory item successful:', addResponse.data);
    
    return true;
  } catch (error) {
    console.log('❌ Inventory API test failed:', error.response?.data || error.message);
    return false;
  }
}

async function testDashboardAPI(token) {
  try {
    console.log('🔍 Testing dashboard API...');
    const headers = { Authorization: `Bearer ${token}` };
    
    const response = await axios.get(`${BASE_URL}/api/dashboard/stats`, { headers });
    console.log('✅ Dashboard stats successful:', response.data);
    
    return true;
  } catch (error) {
    console.log('❌ Dashboard API test failed:', error.response?.data || error.message);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting Node.js Backend Tests\n');
  
  const results = {
    healthCheck: false,
    registration: false,
    login: false,
    inventory: false,
    dashboard: false
  };
  
  // Test health check
  results.healthCheck = await testHealthCheck();
  console.log('');
  
  // Test user registration
  results.registration = await testUserRegistration();
  console.log('');
  
  // Test user login
  const token = await testUserLogin();
  results.login = !!token;
  console.log('');
  
  if (token) {
    // Test inventory API
    results.inventory = await testInventoryAPI(token);
    console.log('');
    
    // Test dashboard API
    results.dashboard = await testDashboardAPI(token);
    console.log('');
  }
  
  // Summary
  console.log('📊 Test Results Summary:');
  console.log('========================');
  Object.entries(results).forEach(([test, passed]) => {
    console.log(`${passed ? '✅' : '❌'} ${test}: ${passed ? 'PASSED' : 'FAILED'}`);
  });
  
  const allPassed = Object.values(results).every(result => result);
  console.log(`\n🎯 Overall: ${allPassed ? 'ALL TESTS PASSED' : 'SOME TESTS FAILED'}`);
  
  if (allPassed) {
    console.log('\n🎉 Node.js backend is working correctly!');
  } else {
    console.log('\n⚠️  Some tests failed. Check the server logs and configuration.');
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { runTests, testHealthCheck, testUserRegistration, testUserLogin };
