import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { message, context } = await request.json()

    // Mock AI response generation
    const response = {
      message:
        "Thank you for your order! I have 2 liters of milk and 1 loaf of bread available. The total comes to ₹70. Would you like me to arrange delivery?",
      actions: [
        { type: "create_order", data: { items: ["milk", "bread"], total: 70 } },
        { type: "check_inventory", data: { items: ["milk", "bread"] } },
      ],
      confidence: 0.92,
    }

    return NextResponse.json({
      success: true,
      data: response,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to generate AI response" }, { status: 500 })
  }
}
