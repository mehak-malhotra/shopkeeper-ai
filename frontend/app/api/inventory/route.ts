import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch all inventory items
export async function GET(request: NextRequest) {
  try {
    // Mock inventory data
    const inventory = [
      { id: "1", name: "Milk", price: 25, quantity: 2, minStock: 10, category: "Dairy" },
      { id: "2", name: "Bread", price: 20, quantity: 5, minStock: 15, category: "Bakery" },
      { id: "3", name: "Eggs", price: 60, quantity: 8, minStock: 20, category: "Dairy" },
    ]

    return NextResponse.json({
      success: true,
      data: inventory,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch inventory" }, { status: 500 })
  }
}

// POST - Add new inventory item
export async function POST(request: NextRequest) {
  try {
    const { name, price, quantity, minStock, category } = await request.json()

    const newItem = {
      id: Date.now().toString(),
      name,
      price: Number.parseFloat(price),
      quantity: Number.parseInt(quantity),
      minStock: Number.parseInt(minStock) || 5,
      category: category || "General",
      createdAt: new Date().toISOString(),
    }

    return NextResponse.json({
      success: true,
      data: newItem,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to add inventory item" }, { status: 500 })
  }
}
