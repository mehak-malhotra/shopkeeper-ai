import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch call logs
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = searchParams.get("limit")
    const status = searchParams.get("status")

    const calls = [
      {
        id: "CALL-001",
        customerPhone: "+1234567890",
        customerName: "John Doe",
        duration: 180,
        timestamp: new Date().toISOString(),
        status: "completed",
        transcript: "Hello, I would like to order some groceries...",
        summary: "Customer ordered milk and bread",
        orderId: "ORD-001",
      },
    ]

    return NextResponse.json({
      success: true,
      data: calls,
      total: calls.length,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch call logs" }, { status: 500 })
  }
}

// POST - Create new call record
export async function POST(request: NextRequest) {
  try {
    const callData = await request.json()

    const newCall = {
      id: `CALL-${Date.now()}`,
      ...callData,
      timestamp: new Date().toISOString(),
    }

    return NextResponse.json({
      success: true,
      data: newCall,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to create call record" }, { status: 500 })
  }
}
