"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Search, Phone, Clock, FileText, Play, ExternalLink } from "lucide-react"

interface CallRecord {
  id: string
  customerPhone: string
  customerName?: string
  duration: number // in seconds
  timestamp: string
  status: "completed" | "missed" | "failed"
  transcript?: string
  summary?: string
  orderId?: string
  audioUrl?: string
}

export default function CallsPage() {
  const [calls, setCalls] = useState<CallRecord[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null)
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false)

  useEffect(() => {
    // Mock data - in real app, fetch from your Flask backend
    setCalls([
      {
        id: "CALL-001",
        customerPhone: "+1234567890",
        customerName: "John Doe",
        duration: 180,
        timestamp: "2024-01-10T10:30:00Z",
        status: "completed",
        transcript:
          "Hello, I would like to order some groceries. I need 2 liters of milk, 1 loaf of bread, and a dozen eggs. Can you deliver it by evening?",
        summary: "Customer ordered milk (2L), bread (1 loaf), and eggs (1 dozen). Requested evening delivery.",
        orderId: "ORD-001",
        audioUrl: "/audio/call-001.mp3",
      },
      {
        id: "CALL-002",
        customerPhone: "+1234567891",
        customerName: "Jane Smith",
        duration: 120,
        timestamp: "2024-01-10T09:15:00Z",
        status: "completed",
        transcript: "Hi, I need 1 kg rice and 1 liter cooking oil. What's the total price?",
        summary: "Customer inquired about rice (1kg) and cooking oil (1L). Provided pricing information.",
        orderId: "ORD-002",
      },
      {
        id: "CALL-003",
        customerPhone: "+1234567892",
        duration: 45,
        timestamp: "2024-01-10T08:45:00Z",
        status: "completed",
        transcript: "I want to order sugar and tea packets.",
        summary: "Customer ordered sugar and tea packets.",
        orderId: "ORD-003",
      },
      {
        id: "CALL-004",
        customerPhone: "+1234567893",
        duration: 0,
        timestamp: "2024-01-10T08:30:00Z",
        status: "missed",
        summary: "Missed call - no voicemail left",
      },
      {
        id: "CALL-005",
        customerPhone: "+1234567894",
        duration: 90,
        timestamp: "2024-01-10T11:00:00Z",
        status: "completed",
        transcript: "Hello, I need 2 kg rice and 1 kg sugar for my store.",
        summary: "Customer ordered rice (2kg) and sugar (1kg).",
        orderId: "ORD-005",
      },
    ])
  }, [])

  const filteredCalls = calls.filter(
    (call) =>
      call.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.customerPhone.includes(searchTerm) ||
      (call.customerName && call.customerName.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (call.orderId && call.orderId.toLowerCase().includes(searchTerm.toLowerCase())),
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800"
      case "missed":
        return "bg-yellow-100 text-yellow-800"
      case "failed":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const formatDuration = (seconds: number) => {
    if (seconds === 0) return "0:00"
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  const formatDateTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return {
      date: date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      }),
      time: date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    }
  }

  const getCallStats = () => {
    return {
      total: calls.length,
      completed: calls.filter((c) => c.status === "completed").length,
      missed: calls.filter((c) => c.status === "missed").length,
      failed: calls.filter((c) => c.status === "failed").length,
      totalDuration: calls.reduce((sum, call) => sum + call.duration, 0),
    }
  }

  const stats = getCallStats()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Call & Transcript Logs</h1>
        <p className="text-muted-foreground mt-2">Review customer calls and AI-generated transcripts</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-600">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-yellow-600">Missed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.missed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-600">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(stats.totalDuration)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="Search calls, customers, or order IDs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Calls List */}
      <div className="space-y-4">
        {filteredCalls.map((call) => {
          const dateTime = formatDateTime(call.timestamp)
          return (
            <Card key={call.id}>
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">{call.id}</h3>
                      <Badge className={getStatusColor(call.status)}>{call.status}</Badge>
                      {call.orderId && (
                        <Badge variant="outline">
                          <ExternalLink className="h-3 w-3 mr-1" />
                          {call.orderId}
                        </Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">
                          {call.customerPhone}
                          {call.customerName && <span className="text-gray-600 ml-2">({call.customerName})</span>}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span className="text-sm text-gray-600">
                          {dateTime.date} at {dateTime.time}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">Duration: {formatDuration(call.duration)}</span>
                      </div>
                    </div>

                    {call.summary && (
                      <div className="mb-3">
                        <p className="text-sm text-gray-600 mb-1">Summary:</p>
                        <p className="text-sm bg-gray-50 p-2 rounded">{call.summary}</p>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col gap-2 lg:w-48">
                    {call.transcript && (
                      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm" onClick={() => setSelectedCall(call)}>
                            <FileText className="h-4 w-4 mr-2" />
                            View Transcript
                          </Button>
                        </DialogTrigger>
                      </Dialog>
                    )}

                    {call.audioUrl && (
                      <Button variant="outline" size="sm">
                        <Play className="h-4 w-4 mr-2" />
                        Play Audio
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Call Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Call Transcript - {selectedCall?.id}</DialogTitle>
            <DialogDescription>AI-generated transcript and call details</DialogDescription>
          </DialogHeader>

          {selectedCall && (
            <div className="space-y-6">
              {/* Call Info */}
              <div>
                <h4 className="font-semibold mb-2">Call Information</h4>
                <div className="bg-muted p-4 rounded-lg space-y-2">
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-gray-500" />
                    <span>{selectedCall.customerPhone}</span>
                    {selectedCall.customerName && <span className="text-gray-600">({selectedCall.customerName})</span>}
                  </div>
                  <p>
                    <strong>Date & Time:</strong> {formatDateTime(selectedCall.timestamp).date} at{" "}
                    {formatDateTime(selectedCall.timestamp).time}
                  </p>
                  <p>
                    <strong>Duration:</strong> {formatDuration(selectedCall.duration)}
                  </p>
                  <div className="flex items-center gap-2">
                    <span>
                      <strong>Status:</strong>
                    </span>
                    <Badge className={getStatusColor(selectedCall.status)}>{selectedCall.status}</Badge>
                  </div>
                  {selectedCall.orderId && (
                    <p>
                      <strong>Related Order:</strong> {selectedCall.orderId}
                    </p>
                  )}
                </div>
              </div>

              {/* Summary */}
              {selectedCall.summary && (
                <div>
                  <h4 className="font-semibold mb-2">AI Summary</h4>
                  <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
                    <p className="text-sm">{selectedCall.summary}</p>
                  </div>
                </div>
              )}

              {/* Transcript */}
              {selectedCall.transcript && (
                <div>
                  <h4 className="font-semibold mb-2">Full Transcript</h4>
                  <div className="bg-muted p-4 rounded-lg max-h-60 overflow-y-auto">
                    <p className="text-sm whitespace-pre-wrap">{selectedCall.transcript}</p>
                  </div>
                </div>
              )}

              {/* Audio Player */}
              {selectedCall.audioUrl && (
                <div>
                  <h4 className="font-semibold mb-2">Audio Recording</h4>
                  <div className="bg-muted p-4 rounded-lg">
                    <audio controls className="w-full">
                      <source src={selectedCall.audioUrl} type="audio/mpeg" />
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {filteredCalls.length === 0 && (
        <div className="text-center py-12">
          <Phone className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No calls found</h3>
          <p className="text-muted-foreground">
            {searchTerm
              ? "Try adjusting your search terms"
              : "Call logs will appear here when customers contact your AI assistant"}
          </p>
        </div>
      )}
    </div>
  )
}
