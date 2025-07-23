import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch user profile
export async function GET(request: NextRequest) {
  try {
    const profile = {
      id: "1",
      email: "shop@example.com",
      shopName: "Corner Store",
      phone: "+1234567890",
      address: "123 Main St",
      ownerName: "John Doe",
    }

    return NextResponse.json({
      success: true,
      data: profile,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch profile" }, { status: 500 })
  }
}

// PUT - Update user profile
export async function PUT(request: NextRequest) {
  try {
    const updateData = await request.json()

    return NextResponse.json({
      success: true,
      data: {
        ...updateData,
        updatedAt: new Date().toISOString(),
      },
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to update profile" }, { status: 500 })
  }
}
