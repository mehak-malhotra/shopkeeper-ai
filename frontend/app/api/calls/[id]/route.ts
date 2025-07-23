import { type NextRequest, NextResponse } from "next/server"

// GET - Fetch specific call
export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params

    const call = {
      id,
      customerPhone: "+1234567890",
      duration: 180,
      timestamp: new Date().toISOString(),
      status: "completed",
      transcript: "Full call transcript...",
      summary: "Call summary",
      audioUrl: `/audio/${id}.mp3`,
    }

    return NextResponse.json({
      success: true,
      data: call,
    })
  } catch (error) {
    return NextResponse.json({ success: false, message: "Failed to fetch call" }, { status: 500 })
  }
}
