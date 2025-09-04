const express = require('express');
const multer = require('multer');
const sharp = require('sharp');
const Tesseract = require('tesseract.js');
const axios = require('axios');
const Fuse = require('fuse.js');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Configure multer for image upload
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'), false);
    }
  }
});

// Preprocess image for better OCR
const preprocessImage = async (imageBuffer) => {
  try {
    // Convert to grayscale and resize if needed
    const processedImage = await sharp(imageBuffer)
      .grayscale()
      .resize(2000, 2000, { 
        fit: 'inside',
        withoutEnlargement: true 
      })
      .normalize()
      .sharpen()
      .png()
      .toBuffer();
    
    return processedImage;
  } catch (error) {
    console.error('Image preprocessing error:', error);
    return imageBuffer; // Return original if preprocessing fails
  }
};

// Extract items from OCR text using Gemini
const extractItemsFromOCRText = async (ocrText) => {
  try {
    const prompt = `You are a smart assistant. Given messy handwritten shopping list text, extract a JSON list of items with names and quantities. If quantity is missing, assume 1. Example output: [{"item": "Moong Dal", "quantity": 2}]. Ignore headers like 'India Market'. Normalize spelling errors.

OCR Text: ${ocrText}

Return only valid JSON array with items and quantities:`;
    
    const headers = {
      'Content-Type': 'application/json'
    };
    
    const params = {
      key: process.env.GEMINI_API_KEY
    };
    
    const geminiData = {
      contents: [{
        role: 'user',
        parts: [{ text: prompt }]
      }]
    };
    
    const response = await axios.post(
      process.env.GEMINI_API_URL,
      geminiData,
      { headers, params }
    );
    
    const geminiReply = response.data.candidates[0].content.parts[0].text;
    
    // Extract JSON from Gemini response
    try {
      const startIdx = geminiReply.indexOf('[');
      const endIdx = geminiReply.lastIndexOf(']') + 1;
      
      if (startIdx !== -1 && endIdx !== 0) {
        const jsonStr = geminiReply.substring(startIdx, endIdx);
        const items = JSON.parse(jsonStr);
        return items;
      } else {
        console.error('No JSON array found in Gemini response:', geminiReply);
        return [];
      }
    } catch (jsonError) {
      console.error('JSON parsing error:', jsonError);
      console.error('Gemini response:', geminiReply);
      return [];
    }
  } catch (error) {
    console.error('Gemini API error:', error);
    return [];
  }
};

// Fuzzy match items with inventory
const fuzzyMatchItems = (requestedItems, inventoryItems) => {
  const matchedItems = [];
  
  // Configure Fuse.js for fuzzy matching
  const fuse = new Fuse(inventoryItems, {
    keys: ['name'],
    threshold: 0.3, // Lower threshold for more strict matching
    includeScore: true
  });
  
  requestedItems.forEach(requestedItem => {
    const itemName = requestedItem.item?.trim();
    const requestedQuantity = requestedItem.quantity || 1;
    
    if (!itemName) return;
    
    // Search for best match
    const searchResults = fuse.search(itemName);
    
    if (searchResults.length > 0) {
      const bestMatch = searchResults[0];
      const inventoryItem = bestMatch.item;
      const score = bestMatch.score;
      
      // Only accept matches with score > 0.7 (70% similarity)
      if (score > 0.7) {
        const availableQuantity = inventoryItem.quantity || 0;
        const fulfilledQuantity = Math.min(requestedQuantity, availableQuantity);
        
        if (fulfilledQuantity > 0) {
          matchedItems.push({
            item_name: inventoryItem.name,
            requested_quantity: requestedQuantity,
            fulfilled_quantity: fulfilledQuantity,
            price: inventoryItem.price || 0,
            total_price: fulfilledQuantity * (inventoryItem.price || 0),
            match_score: Math.round((1 - score) * 100), // Convert to percentage
            available_stock: availableQuantity
          });
        } else {
          console.log(`⚠️ Item '${itemName}' matched to '${inventoryItem.name}' but out of stock`);
        }
      } else {
        console.log(`❌ No good match found for item: ${itemName}`);
      }
    } else {
      console.log(`❌ No match found for item: ${itemName}`);
    }
  });
  
  return matchedItems;
};

// Send notification
const sendNotification = (orderId, customerName, totalItems) => {
  try {
    console.log(`🔔 Notification: New order ${orderId} created for ${customerName} with ${totalItems} items`);
    // In production, this could send email, SMS, or push notification
    return true;
  } catch (error) {
    console.error('❌ Notification error:', error);
    return false;
  }
};

// Image-to-order workflow endpoint
router.post('/', loginRequired, upload.single('image'), async (req, res) => {
  try {
    const user = req.user;
    const { customer_phone, customer_name } = req.body;
    
    // Check if image file is present
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No image file provided'
      });
    }
    
    // Find or create customer
    let customerId = null;
    const customers = user.customers || [];
    let finalCustomerName = customer_name || 'Unknown Customer';
    
    if (customer_phone) {
      const existingCustomer = customers.find(c => c.phone === customer_phone);
      if (existingCustomer) {
        customerId = existingCustomer.customer_id;
        finalCustomerName = existingCustomer.name;
      } else {
        // Create new customer
        customerId = user.getNextCustomerId();
        const newCustomer = {
          customer_id: customerId,
          name: finalCustomerName,
          phone: customer_phone,
          address: '',
          user_email: user.email
        };
        customers.push(newCustomer);
        user.customers = customers;
        await user.save();
      }
    }
    
    // Process the image
    try {
      // Preprocess image
      const processedImageBuffer = await preprocessImage(req.file.buffer);
      
      // Perform OCR
      const { data: { text: ocrText } } = await Tesseract.recognize(
        processedImageBuffer,
        'eng',
        {
          logger: m => console.log(m)
        }
      );
      
      console.log('📝 OCR Text:', ocrText);
      
      if (!ocrText.trim()) {
        return res.status(400).json({
          success: false,
          message: 'No text found in image'
        });
      }
      
      // Extract items using Gemini
      const requestedItems = await extractItemsFromOCRText(ocrText);
      console.log('🛒 Extracted items:', requestedItems);
      
      if (!requestedItems || requestedItems.length === 0) {
        return res.status(400).json({
          success: false,
          message: 'No items could be extracted from image'
        });
      }
      
      // Fuzzy match with inventory
      const inventoryItems = user.inventory || [];
      const matchedItems = fuzzyMatchItems(requestedItems, inventoryItems);
      
      if (!matchedItems || matchedItems.length === 0) {
        return res.status(400).json({
          success: false,
          message: 'No items matched with inventory'
        });
      }
      
      // Calculate order total
      const orderTotal = matchedItems.reduce((sum, item) => sum + item.total_price, 0);
      
      // Generate order ID
      const nextOrderId = user.getNextOrderId();
      const orderIdStr = String(nextOrderId).padStart(4, '0'); // Format as "0001", "0002", etc.
      
      // Create order object
      const orderItems = matchedItems.map(item => ({
        name: item.item_name,
        quantity: item.fulfilled_quantity,
        price: item.price,
        total: item.total_price
      }));
      
      const newOrder = {
        order_id: nextOrderId,
        customer_id: customerId,
        customer_phone: customer_phone,
        customer_name: finalCustomerName,
        items: orderItems,
        total: orderTotal,
        status: 'pending',
        timestamp: new Date().toISOString(),
        notes: `Order created from image upload. OCR text: ${ocrText.substring(0, 100)}...`,
        source: 'image_upload'
      };
      
      // Add order to user's orders
      const orders = user.orders || [];
      orders.push(newOrder);
      user.orders = orders;
      await user.save();
      
      // Update inventory quantities
      const inventoryUpdates = [];
      matchedItems.forEach(item => {
        const itemName = item.item_name;
        const fulfilledQty = item.fulfilled_quantity;
        
        const inventoryItem = inventoryItems.find(invItem => invItem.name === itemName);
        if (inventoryItem) {
          inventoryItem.quantity = Math.max(0, inventoryItem.quantity - fulfilledQty);
          inventoryUpdates.push({
            name: itemName,
            quantity: -fulfilledQty
          });
        }
      });
      
      // Update inventory in database
      user.inventory = inventoryItems;
      await user.save();
      
      // Send notification
      sendNotification(orderIdStr, finalCustomerName, matchedItems.length);
      
      // Prepare response
      const responseData = {
        order_id: orderIdStr,
        customer_name: finalCustomerName,
        customer_phone: customer_phone,
        items: matchedItems,
        total_price: orderTotal,
        status: 'pending',
        timestamp: newOrder.timestamp,
        ocr_text: ocrText,
        extracted_items: requestedItems,
        inventory_updates: inventoryUpdates
      };
      
      res.json({
        success: true,
        message: `Order ${orderIdStr} created successfully from image`,
        data: responseData
      });
      
    } catch (imageError) {
      console.error('❌ Image processing error:', imageError);
      res.status(500).json({
        success: false,
        message: `Image processing error: ${imageError.message}`
      });
    }
    
  } catch (error) {
    console.error('❌ Upload image order error:', error);
    res.status(500).json({
      success: false,
      message: `Server error: ${error.message}`
    });
  }
});

module.exports = router;
