import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const stats = {
      totalOrders: 156,
      pendingOrders: 8,
      lowStockItems: 3,
      totalRevenue: 12450,
      totalProducts: 45,
      completedCalls: 23,
      missedCalls: 2,
      totalCallDuration: 1800,
    }

    return NextResponse.json({
      success: true,
      data: stats,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch dashboard stats" }, { status: 500 })
  }
}
