"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"
import { Search, Phone, Clock, Eye, Filter, ShoppingCart } from "lucide-react"

interface OrderItem {
  name: string
  quantity: number
  price: number
}

interface Order {
  order_id: string
  customer_id: string
  customerPhone: string
  customerName?: string
  items: OrderItem[]
  total: number
  status: "pending" | "confirmed" | "dispatched" | "delivered"
  timestamp: string
  notes?: string
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false)
  const { toast } = useToast()
  const user = JSON.parse(localStorage.getItem("user") || '{}')
  // Add state for customers
  const [customers, setCustomers] = useState<any[]>([])

  useEffect(() => {
    async function fetchOrdersAndCustomers() {
      if (!user.token) return
      // Fetch orders
      const ordersRes = await fetch(`http://localhost:5000/api/orders`, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })
      const ordersData = await ordersRes.json()
      if (ordersData.success) {
        // Convert order_id to string and ensure customer_id exists
        setOrders(ordersData.data.map((o: any) => ({ 
          ...o, 
          order_id: o.order_id?.toString() || o.order_id || '',
          customer_id: o.customer_id || '' 
        })))
      }
      // Fetch customers
      const customersRes = await fetch(`http://localhost:5000/api/customers`, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })
      const customersData = await customersRes.json()
      if (customersData.success) setCustomers(customersData.data)
    }
    fetchOrdersAndCustomers()
  }, [user.token])

  // Helper to get customer name by customer_id
  const getCustomerName = (customer_id: string) => {
    const customer = customers.find((c) => c.customer_id === customer_id)
    return customer ? customer.name : ''
  }

  const filteredOrders = orders.filter((order) => {
    const matchesSearch =
      order.order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customerPhone.includes(searchTerm) ||
      (order.customerName && order.customerName.toLowerCase().includes(searchTerm.toLowerCase())) ||
      order.items.some((item) => item.name.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesStatus = statusFilter === "all" || order.status === statusFilter

    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800"
      case "confirmed":
        return "bg-blue-100 text-blue-800"
      case "dispatched":
        return "bg-purple-100 text-purple-800"
      case "delivered":
        return "bg-green-100 text-green-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const updateOrderStatus = async (orderId: string, newStatus: Order["status"]) => {
    const user = JSON.parse(localStorage.getItem("user") || '{}')
    try {
      const response = await fetch(`http://localhost:5000/api/orders/${orderId}`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ status: newStatus }),
      })
      const data = await response.json()
      if (data.success) {
        setOrders((prev) => prev.map((order) => (order.order_id === orderId ? { ...order, status: newStatus } : order)))
        toast({
          title: "Order status updated",
          description: `Order ${orderId} status changed to ${newStatus}`,
        })
      } else {
        toast({
          title: "Failed to update order",
          description: data.message || "An error occurred.",
          variant: "destructive",
        })
      }
    } catch (err) {
      toast({
        title: "Network error",
        description: "Could not update order status.",
        variant: "destructive",
      })
    }
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

  const getOrderStats = () => {
    return {
      total: orders.length,
      pending: orders.filter((o) => o.status === "pending").length,
      confirmed: orders.filter((o) => o.status === "confirmed").length,
      dispatched: orders.filter((o) => o.status === "dispatched").length,
      delivered: orders.filter((o) => o.status === "delivered").length,
    }
  }

  const stats = getOrderStats()



  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Orders Management</h1>
        <p className="text-muted-foreground mt-2">Track and manage customer orders</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-yellow-600">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-600">Confirmed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.confirmed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-purple-600">Dispatched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats.dispatched}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-600">Delivered</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.delivered}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search orders, customers, or products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-48">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Orders</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="confirmed">Confirmed</SelectItem>
            <SelectItem value="dispatched">Dispatched</SelectItem>
            <SelectItem value="delivered">Delivered</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* All Orders List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">All Orders</h2>
        {filteredOrders.map((order) => {
          const dateTime = formatDateTime(order.timestamp)
          return (
            <Card key={order.order_id}>
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">Order ID: {order.order_id}</h3>
                      <Badge className={getStatusColor(order.status)}>{order.status}</Badge>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">
                          {order.customerPhone}
                          {getCustomerName(order.customer_id) && <span className="text-black-600 ml-2">({getCustomerName(order.customer_id)})</span>}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-black-500" />
                        <span className="text-sm text-black-600">
                          {dateTime.date} at {dateTime.time}
                        </span>
                      </div>
                    </div>

                    <div className="mb-3">
                      <p className="text-sm text-gray-600 mb-1">Items:</p>
                      <p className="text-sm">
                        {order.items.map((item) => `${item.name} (${item.quantity})`).join(", ")}
                      </p>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-lg">Total: ₹{order.total}</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 lg:w-48">
                    <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => setSelectedOrder(order)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </DialogTrigger>
                    </Dialog>

                    <Select
                      value={order.status}
                      onValueChange={(value: Order["status"]) => updateOrderStatus(order.order_id, value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="confirmed">Confirmed</SelectItem>
                        <SelectItem value="dispatched">Dispatched</SelectItem>
                        <SelectItem value="delivered">Delivered</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Order Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-2xl" style={{ color: '#000' }}>
          <DialogHeader>
            <DialogTitle style={{ color: '#000' }}>Order Details - {selectedOrder?.order_id}</DialogTitle>
            <DialogDescription style={{ color: '#000' }}>Complete information about this order</DialogDescription>
          </DialogHeader>

          {selectedOrder && (
            <div className="space-y-6" style={{ color: '#000' }}>
              {/* Order and Customer Info */}
              <div>
                <h4 className="font-semibold mb-2" style={{ color: '#000' }}>Order & Customer Information</h4>
                <div className="bg-gray-50 p-4 rounded-lg space-y-2" style={{ color: '#000' }}>
                  <div className="flex items-center gap-2">
                    <strong style={{ color: '#000' }}>Order ID:</strong>
                    <span style={{ color: '#000' }}>{selectedOrder.order_id}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <strong style={{ color: '#000' }}>Customer ID:</strong>
                    <span style={{ color: '#000' }}>{selectedOrder.customer_id || 'N/A'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-black" />
                    <span style={{ color: '#000' }}>{selectedOrder.customerPhone}</span>
                  </div>
                  {getCustomerName(selectedOrder.customer_id) && (
                    <p style={{ color: '#000' }}>
                      <strong style={{ color: '#000' }}>Customer Name:</strong> {getCustomerName(selectedOrder.customer_id)}
                    </p>
                  )}
                  <p style={{ color: '#000' }}>
                    <strong style={{ color: '#000' }}>Order Date:</strong> {formatDateTime(selectedOrder.timestamp).date} at{" "}
                    {formatDateTime(selectedOrder.timestamp).time}
                  </p>
                  <div className="flex items-center gap-2">
                    <span style={{ color: '#000' }}>
                      <strong style={{ color: '#000' }}>Status:</strong>
                    </span>
                    <Badge className={getStatusColor(selectedOrder.status)} style={{ color: '#000' }}>{selectedOrder.status}</Badge>
                  </div>
                </div>
              </div>

              {/* Order Items */}
              <div>
                <h4 className="font-semibold mb-2">Order Items</h4>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left p-3 font-medium">Product</th>
                        <th className="text-center p-3 font-medium">Quantity</th>
                        <th className="text-right p-3 font-medium">Price</th>
                        <th className="text-right p-3 font-medium">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedOrder.items.map((item, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-3">{item.name}</td>
                          <td className="p-3 text-center">{item.quantity}</td>
                          <td className="p-3 text-right">₹{item.price}</td>
                          <td className="p-3 text-right">₹{item.quantity * item.price}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50 border-t">
                      <tr>
                        <td colSpan={3} className="p-3 font-semibold text-right">
                          Total:
                        </td>
                        <td className="p-3 font-semibold text-right">₹{selectedOrder.total}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Notes */}
              {selectedOrder.notes && (
                <div>
                  <h4 className="font-semibold mb-2">Notes</h4>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm">{selectedOrder.notes}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {filteredOrders.length === 0 && (
        <div className="text-center py-12">
          <ShoppingCart className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No orders found</h3>
          <p className="text-muted-foreground">
            {searchTerm || statusFilter !== "all"
              ? "Try adjusting your search or filter criteria"
              : "Orders will appear here when customers place them"}
          </p>
        </div>
      )}
    </div>
  )
}
