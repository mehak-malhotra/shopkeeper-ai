import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch specific order
export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params

    const order = {
      id,
      customerPhone: "+1234567890",
      customerName: "John Doe",
      items: [{ productName: "Milk", quantity: 2, price: 25 }],
      total: 50,
      status: "pending",
      timestamp: new Date().toISOString(),
    }

    return NextResponse.json({
      success: true,
      data: order,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch order" }, { status: 500 })
  }
}

// PUT - Update order status
export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params
    const { status, ...updateData } = await request.json()

    return NextResponse.json({
      success: true,
      data: {
        id,
        status,
        ...updateData,
        updatedAt: new Date().toISOString(),
      },
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to update order" }, { status: 500 })
  }
}
