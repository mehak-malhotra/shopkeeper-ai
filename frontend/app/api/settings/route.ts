import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch app settings
export async function GET(request: NextRequest) {
  try {
    const settings = {
      notifications: {
        orderAlerts: true,
        lowStockAlerts: true,
        callNotifications: true,
        emailNotifications: false,
      },
      ai: {
        autoProcessCalls: true,
        responseDelay: 2,
        confidenceThreshold: 0.8,
      },
      business: {
        operatingHours: {
          start: "09:00",
          end: "21:00",
        },
        deliveryRadius: 5,
        minimumOrderValue: 50,
      },
    }

    return NextResponse.json({
      success: true,
      data: settings,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch settings" }, { status: 500 })
  }
}

// PUT - Update settings
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
    return NextResponse.json({ success: false, message: "Failed to update settings" }, { status: 500 })
  }
}
