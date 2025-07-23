import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const period = searchParams.get("period") || "week"

    const salesData = {
      period,
      totalSales: 12450,
      totalOrders: 156,
      averageOrderValue: 79.8,
      topProducts: [
        { name: "Milk", quantity: 45, revenue: 1125 },
        { name: "Bread", quantity: 38, revenue: 760 },
        { name: "Rice", quantity: 25, revenue: 2000 },
      ],
      dailyBreakdown: [
        { date: "2024-01-01", sales: 1200, orders: 15 },
        { date: "2024-01-02", sales: 1800, orders: 22 },
      ],
    }

    return NextResponse.json({
      success: true,
      data: salesData,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch sales report" }, { status: 500 })
  }
}
