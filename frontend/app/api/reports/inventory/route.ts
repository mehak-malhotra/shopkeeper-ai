import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const inventoryReport = {
      totalProducts: 45,
      lowStockItems: 3,
      outOfStockItems: 1,
      totalValue: 25000,
      categories: [
        { name: "Dairy", count: 8, value: 5000 },
        { name: "Bakery", count: 12, value: 3000 },
        { name: "Grains", count: 15, value: 12000 },
      ],
      reorderSuggestions: [
        { name: "Milk", currentStock: 2, suggestedOrder: 20 },
        { name: "Bread", currentStock: 5, suggestedOrder: 25 },
      ],
    }

    return NextResponse.json({
      success: true,
      data: inventoryReport,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch inventory report" }, { status: 500 })
  }
}
