import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch notifications
export async function GET(request: NextRequest) {
  try {
    const notifications = [
      {
        id: "1",
        type: "order",
        title: "New Order Received",
        message: "Order ORD-001 from +1234567890",
        timestamp: new Date().toISOString(),
        read: false,
      },
      {
        id: "2",
        type: "inventory",
        title: "Low Stock Alert",
        message: "Milk is running low (2 items left)",
        timestamp: new Date().toISOString(),
        read: false,
      },
    ]

    return NextResponse.json({
      success: true,
      data: notifications,
      unreadCount: notifications.filter((n) => !n.read).length,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch notifications" }, { status: 500 })
  }
}

// PUT - Mark notification as read
export async function PUT(request: NextRequest) {
  try {
    const { id } = await request.json()

    return NextResponse.json({
      success: true,
      message: `Notification ${id} marked as read`,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to update notification" }, { status: 500 })
  }
}
