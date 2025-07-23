import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { shopName, email, phone, password } = await request.json()

    // Mock registration logic
    const user = {
      id: Date.now().toString(),
      email,
      shopName,
      phone,
      token: "mock-jwt-token",
      createdAt: new Date().toISOString(),
    }

    return NextResponse.json({
      success: true,
      user,
      token: user.token,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Registration failed" }, { status: 500 })
  }
}
