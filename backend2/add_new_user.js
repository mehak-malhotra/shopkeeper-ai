const axios = require('axios');

const BACKEND_URL = 'http://localhost:5000/api/auth/register';

const mockUser = {
  email: 'test@shopkeeper.com',
  password: 'testpassword123',
  name: 'Test Shop',
  phone: '+1234567890',
  ownerName: 'John Doe',
  address: '123 Test Street, Test City'
};

async function addNewUser() {
  console.log('Adding new user to backend...');
  console.log(`Email: ${mockUser.email}`);
  console.log(`Password: ${mockUser.password}`);
  console.log(`Shop Name: ${mockUser.name}`);
  console.log(`Owner: ${mockUser.ownerName}`);
  
  try {
    const response = await axios.post(BACKEND_URL, mockUser);
    
    console.log(`\nStatus Code: ${response.status}`);
    console.log(`Response: ${JSON.stringify(response.data, null, 2)}`);
    
    if (response.status === 200 || response.status === 201) {
      console.log('✅ User registered successfully!');
      console.log('You can now login with:');
      console.log(`Email: ${mockUser.email}`);
      console.log(`Password: ${mockUser.password}`);
    } else {
      console.log('❌ Failed to register user.');
    }
    
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('❌ Connection error! Make sure your Node.js backend is running on http://localhost:5000');
    } else if (error.response) {
      console.log(`❌ Server error: ${error.response.status} - ${error.response.data.message || error.response.statusText}`);
    } else {
      console.log(`❌ Error: ${error.message}`);
    }
  }
}

if (require.main === module) {
  addNewUser();
}

module.exports = { addNewUser, mockUser };
