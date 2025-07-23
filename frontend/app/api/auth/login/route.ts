import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    // Mock authentication logic
    if (email === "shop@example.com" && password === "password") {
      const user = {
        id: "1",
        email: email,
        shopName: "Corner Store",
        phone: "+1234567890",
        token: "mock-jwt-token",
      }

      return NextResponse.json({
        success: true,
        user,
        token: user.token,
      })
    }

    return NextResponse.json({ success: false, message: "Invalid credentials" }, { status: 401 })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Login failed" }, { status: 500 })
  }
}
