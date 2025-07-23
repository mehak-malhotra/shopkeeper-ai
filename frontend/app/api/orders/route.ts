import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch all orders
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get("status")
    const limit = searchParams.get("limit")

    // Mock orders data
    const orders = [
      {
        id: "ORD-001",
        customerPhone: "+1234567890",
        customerName: "John Doe",
        items: [
          { productName: "Milk", quantity: 2, price: 25 },
          { productName: "Bread", quantity: 1, price: 20 },
        ],
        total: 70,
        status: "pending",
        timestamp: new Date().toISOString(),
      },
    ]

    return NextResponse.json({
      success: true,
      data: orders,
      total: orders.length,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch orders" }, { status: 500 })
  }
}

// POST - Create new order
export async function POST(request: NextRequest) {
  try {
    const orderData = await request.json()

    const newOrder = {
      id: `ORD-${Date.now()}`,
      ...orderData,
      status: "pending",
      timestamp: new Date().toISOString(),
    }

    return NextResponse.json({
      success: true,
      data: newOrder,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to create order" }, { status: 500 })
  }
}
