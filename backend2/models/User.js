const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: [true, 'Email is required'],
    unique: true,
    lowercase: true,
    trim: true,
    match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, 'Please enter a valid email']
  },
  password: {
    type: String,
    required: [true, 'Password is required'],
    minlength: [6, 'Password must be at least 6 characters long']
  },
  name: {
    type: String,
    required: [true, 'Shop name is required'],
    trim: true
  },
  phone: {
    type: String,
    trim: true
  },
  ownerName: {
    type: String,
    trim: true
  },
  address: {
    type: String,
    trim: true
  },
  inventory: [{
    name: {
      type: String,
      required: true,
      trim: true
    },
    quantity: {
      type: Number,
      required: true,
      min: 0
    },
    price: {
      type: Number,
      required: true,
      min: 0
    },
    category: {
      type: String,
      default: 'General',
      trim: true
    },
    minStock: {
      type: Number,
      default: 5,
      min: 0
    }
  }],
  orders: [{
    order_id: {
      type: Number,
      required: true
    },
    customer_id: {
      type: Number
    },
    customer_phone: {
      type: String,
      trim: true
    },
    customer_name: {
      type: String,
      trim: true
    },
    items: [{
      name: {
        type: String,
        required: true,
        trim: true
      },
      quantity: {
        type: Number,
        required: true,
        min: 1
      },
      price: {
        type: Number,
        required: true,
        min: 0
      },
      total: {
        type: Number,
        required: true,
        min: 0
      }
    }],
    total: {
      type: Number,
      required: true,
      min: 0
    },
    status: {
      type: String,
      enum: ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'],
      default: 'pending'
    },
    timestamp: {
      type: String,
      required: true
    },
    notes: {
      type: String,
      trim: true
    },
    source: {
      type: String,
      default: 'manual'
    }
  }],
  customers: [{
    customer_id: {
      type: Number,
      required: true
    },
    name: {
      type: String,
      required: true,
      trim: true
    },
    phone: {
      type: String,
      required: true,
      trim: true
    },
    address: {
      type: String,
      trim: true
    },
    user_email: {
      type: String,
      required: true
    }
  }]
}, {
  timestamps: true
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(12);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Compare password method
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

// Get next customer ID
userSchema.methods.getNextCustomerId = function() {
  const customers = this.customers || [];
  if (customers.length === 0) return 1;
  
  const maxId = Math.max(...customers.map(c => c.customer_id || 0));
  return maxId + 1;
};

// Get next order ID
userSchema.methods.getNextOrderId = function() {
  const orders = this.orders || [];
  if (orders.length === 0) return 1;
  
  const maxId = Math.max(...orders.map(o => o.order_id || 0));
  return maxId + 1;
};

// Remove password from JSON output
userSchema.methods.toJSON = function() {
  const userObject = this.toObject();
  delete userObject.password;
  return userObject;
};

module.exports = mongoose.model('User', userSchema);
