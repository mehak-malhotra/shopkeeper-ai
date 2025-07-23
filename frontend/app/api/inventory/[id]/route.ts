import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch specific inventory item
export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params

    // Mock fetch single item
    const item = {
      id,
      name: "Milk",
      price: 25,
      quantity: 2,
      minStock: 10,
      category: "Dairy",
    }

    return NextResponse.json({
      success: true,
      data: item,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch inventory item" }, { status: 500 })
  }
}

// PUT - Update inventory item
export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params
    const updateData = await request.json()

    return NextResponse.json({
      success: true,
      data: { id, ...updateData, updatedAt: new Date().toISOString() },
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to update inventory item" }, { status: 500 })
  }
}

// DELETE - Delete inventory item
export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params

    return NextResponse.json({
      success: true,
      message: `Inventory item ${id} deleted successfully`,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to delete inventory item" }, { status: 500 })
  }
}
