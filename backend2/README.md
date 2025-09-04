# Shopkeeper AI - Node.js Backend

This is the Node.js implementation of the Shopkeeper AI backend, providing the same functionality as the Python Flask backend but built with Express.js and modern JavaScript.

## Features

- **Authentication**: User registration, login, and JWT-based authentication
- **Inventory Management**: CRUD operations for inventory items
- **Order Management**: Create, read, update, and delete orders
- **Customer Management**: Customer database and lookup functionality
- **Profile Management**: User profile updates and password changes
- **Dashboard Analytics**: Statistics and insights for business operations
- **AI Chatbot**: Integration with Google Gemini for intelligent customer service
- **Image Processing**: OCR functionality for handwritten shopping lists
- **Fuzzy Matching**: Smart item matching between requests and inventory

## Tech Stack

- **Runtime**: Node.js (v18+)
- **Framework**: Express.js
- **Database**: MongoDB with Mongoose ODM
- **Authentication**: JWT tokens
- **Image Processing**: Sharp, Tesseract.js
- **AI Integration**: Google Gemini API
- **Fuzzy Matching**: Fuse.js
- **Security**: Helmet, CORS, Rate Limiting

## Installation

1. **Clone and navigate to the backend2 directory**:
   ```bash
   cd backend2
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/shop_db
   JWT_SECRET=your-super-secret-jwt-key-here
   GEMINI_API_KEY=your-gemini-api-key-here
   GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
   PORT=5000
   NODE_ENV=development
   FRONTEND_URL=http://localhost:3000
   ```

4. **Start the server**:
   ```bash
   # Development mode with auto-reload
   npm run dev
   
   # Production mode
   npm start
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Inventory Management
- `GET /api/inventory` - Get all inventory items
- `POST /api/inventory` - Add new inventory item
- `PUT /api/inventory/:itemName` - Update inventory item
- `DELETE /api/inventory/:itemName` - Delete inventory item
- `POST /api/inventory/update-quantities` - Bulk update quantities

### Order Management
- `GET /api/orders` - Get all orders
- `POST /api/orders` - Create new order
- `POST /api/orders/direct` - Create direct order
- `GET /api/orders/:orderId` - Get specific order
- `PUT /api/orders/:orderId` - Update order
- `DELETE /api/orders/:orderId` - Delete order

### Customer Management
- `GET /api/customers` - Get all customers
- `POST /api/customers/add` - Add new customer
- `POST /api/customers/find-by-phone` - Find customer by phone
- `PUT /api/customers/:customerId` - Update customer
- `DELETE /api/customers/:customerId` - Delete customer

### Profile Management
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update profile
- `PUT /api/profile/password` - Update password
- `DELETE /api/profile` - Delete account

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/activity` - Get recent activity
- `GET /api/dashboard/alerts` - Get inventory alerts

### AI Chatbot
- `POST /api/chatbot` - Chat with AI assistant
- `GET /api/chatbot/data` - Get chatbot data
- `POST /api/chatbot/process-call` - Process voice calls
- `POST /api/chatbot/generate-response` - Generate AI responses

### Image Processing
- `POST /api/upload-image-order` - Upload image and create order from OCR

## Testing

### Add Test User
Run the test script to add a sample user:
```bash
node add_new_user.js
```

### Health Check
Check if the server is running:
```bash
curl http://localhost:5000/health
```

## Project Structure

```
backend2/
├── app.js                 # Main application file
├── package.json           # Dependencies and scripts
├── env.example           # Environment variables template
├── add_new_user.js       # Test script for adding users
├── README.md             # This file
├── config/
│   └── database.js       # MongoDB connection configuration
├── middleware/
│   └── auth.js           # Authentication middleware
├── models/
│   └── User.js           # User data model
└── routes/
    ├── auth.js           # Authentication routes
    ├── inventory.js      # Inventory management routes
    ├── orders.js         # Order management routes
    ├── customers.js      # Customer management routes
    ├── profile.js        # Profile management routes
    ├── dashboard.js      # Dashboard and analytics routes
    ├── chatbot.js        # AI chatbot routes
    └── image.js          # Image processing routes
```

## Key Differences from Python Backend

1. **Authentication**: Uses JWT tokens instead of simple token storage
2. **Database**: Uses Mongoose ODM instead of PyMongo
3. **Image Processing**: Uses Sharp and Tesseract.js instead of PIL and pytesseract
4. **Fuzzy Matching**: Uses Fuse.js instead of RapidFuzz
5. **Error Handling**: Express.js error handling middleware
6. **Security**: Built-in security with Helmet and rate limiting

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URI` | MongoDB connection string | Yes |
| `JWT_SECRET` | Secret key for JWT tokens | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GEMINI_API_URL` | Gemini API endpoint URL | Yes |
| `PORT` | Server port (default: 5000) | No |
| `NODE_ENV` | Environment (development/production) | No |
| `FRONTEND_URL` | Frontend URL for CORS | No |

## Development

### Scripts
- `npm start` - Start production server
- `npm run dev` - Start development server with nodemon
- `npm test` - Run tests (when implemented)

### Adding New Features
1. Create route files in `routes/` directory
2. Add middleware in `middleware/` directory if needed
3. Create models in `models/` directory
4. Import and use routes in `app.js`

## Production Deployment

1. Set `NODE_ENV=production`
2. Use a process manager like PM2
3. Set up reverse proxy with Nginx
4. Configure SSL certificates
5. Set up monitoring and logging

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**: Check MONGO_URI and network connectivity
2. **JWT Secret Error**: Ensure JWT_SECRET is set and secure
3. **Gemini API Error**: Verify API key and endpoint URL
4. **Image Processing Error**: Check Tesseract.js installation and image format

### Logs
Check console output for detailed error messages and debugging information.

## License

MIT License - see LICENSE file for details.
