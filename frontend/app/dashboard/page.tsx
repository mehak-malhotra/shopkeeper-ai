"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ShoppingCart, Package, AlertTriangle, TrendingUp, Clock, ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import emailjs from '@emailjs/browser';

interface DashboardStats {
  totalOrders: number
  pendingOrders: number
  lowStockItems: number
  totalRevenue: number
}

interface RecentOrder {
  order_id: string
  customerPhone: string
  items: any[]
  total: number
  status: "pending" | "confirmed" | "dispatched" | "delivered"
  timestamp: string
}

interface LowStockItem {
  id: string
  name: string
  currentStock: number
  minStock: number
}

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const [stats, setStats] = useState<DashboardStats>({
    totalOrders: 0,
    pendingOrders: 0,
    lowStockItems: 0,
    totalRevenue: 0,
    dangerStockItems: 0,
    dangerStock: 0,
  })
  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([])
  const [lowStockItems, setLowStockItems] = useState<LowStockItem[]>([])
  const [dangerStockItems, setDangerStockItems] = useState<LowStockItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    const userData = localStorage.getItem("user")
    if (userData) {
      setUser(JSON.parse(userData))
    }
  }, [])

  useEffect(() => {
    const fetchDashboard = async () => {
      if (!user?.token) return
      setLoading(true)
      setError(null)
      try {
        // Fetch stats
        const statsRes = await fetch(`http://localhost:5000/api/dashboard/stats`, {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        })
        const statsData = await statsRes.json()
        if (statsData.success) setStats(statsData.data)
        else throw new Error(statsData.message || "Failed to fetch stats")

        // Fetch recent orders
        const ordersRes = await fetch(`http://localhost:5000/api/orders`, {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        })
        const ordersData = await ordersRes.json()
        if (ordersData.success) {
          // Sort by timestamp desc, take latest 3
          const sorted = ordersData.data.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          setRecentOrders(sorted.slice(0, 3))
        } else throw new Error(ordersData.message || "Failed to fetch orders")

        // Fetch inventory and filter low stock
        const invRes = await fetch(`http://localhost:5000/api/inventory`, {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        })
        const invData = await invRes.json()
        if (invData.success) {
          const lowStock = invData.data
            .filter((item: any) => item.quantity <= item.minStock)
            .map((item: any) => ({
              id: item.name,
              name: item.name,
              currentStock: item.quantity,
              minStock: item.minStock
            }))
            const dangerStock = invData.data
            .filter((item: any) => item.quantity < item.minStock * 0.2)
            .map((item: any) => ({
              id: item.name,
              name: item.name,
              currentStock: item.quantity,
              minStock: item.minStock,
              supplyemail: item.supplyemail || " "
            }))
            
            setLowStockItems(lowStock.slice(0, 3))
            setDangerStockItems(dangerStock.slice(0, 3))

          for(let i=0;i<dangerStock.length;i++){

            const templateParams = {  // Match these keys to your EmailJS template variables
              email: dangerStock[i].supplyemail,
              message: `Order ${dangerStock[i].minStock*2} ${dangerStock[i].name}`,
              // Add other parameters as defined in your EmailJS template
            };
            try {
              const result = await emailjs.send(
                'Healgrow',
                'template_bhal623',
                templateParams,
                { publicKey: 'YEqgBysf27FVajS9s' }
              );
              console.log('Email successfully sent!', result.text);
              alert('Message Sent Successfully!');
            } catch (error) {
              console.error('Failed to send email:', error.text);
              alert('Failed to send message. Please try again.');
            }
          }
            
        } else throw new Error(invData.message || "Failed to fetch inventory")
      } catch (err: any) {
        setError(err.message || "Unknown error")
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [user?.token])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-50 text-yellow-700 border-yellow-200"
      case "confirmed":
        return "bg-blue-50 text-blue-700 border-blue-200"
      case "dispatched":
        return "bg-purple-50 text-purple-700 border-purple-200"
      case "delivered":
        return "bg-green-50 text-green-700 border-green-200"
      default:
        return "bg-gray-50 text-gray-700 border-gray-200"
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <div className="space-y-8">
      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Loading dashboard...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-600">{error}</div>
      ) : (
        <>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Good morning, {user?.name || "Shopkeeper"}</h1>
            <p className="text-muted-foreground">Here's what's happening with your store today.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Orders</CardTitle>
                <ShoppingCart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalOrders}</div>
                <p className="text-xs text-green-600 font-medium">+12% from last month</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Pending Orders</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.pendingOrders}</div>
                <p className="text-xs text-muted-foreground">Needs attention</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Low Stock</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.lowStockItems}</div>
                <p className="text-xs text-muted-foreground">Items need restocking</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Danger Stock</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dangerStockItems.length}</div>
                <p className="text-xs text-muted-foreground">Items are in danger</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Revenue</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₹{stats.totalRevenue.toLocaleString()}</div>
                <p className="text-xs text-green-600 font-medium">+8% from last month</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Recent Orders</CardTitle>
                    <CardDescription>Latest customer orders</CardDescription>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/orders")}>
                    View all
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentOrders.map((order) => (
                    <div key={order.order_id} className="flex items-center justify-between p-4 rounded-lg border bg-card">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium">{order.order_id}</span>
                          <Badge variant="outline" className={getStatusColor(order.status)}>
                            {order.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-1">
                          {order.items.map((item: any) => `${item.name} (${item.quantity})`).join(", ")}
                        </p>
                        <p className="text-xs text-muted-foreground">{formatTime(order.timestamp)}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">₹{order.total}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Low Stock Alerts</CardTitle>
                    <CardDescription>Items that need restocking</CardDescription>
                  </div>
                  <Button variant="ghost" size="sm">
                    View all
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {lowStockItems.map((item) => (
                    <div
                      key={item.name}
                      className="flex items-center justify-between p-4 rounded-lg border border-red-500 bg-gray-900"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Package className="h-4 w-4 text-red-400" />
                          <span className="font-medium text-red-300">{item.name}</span>
                        </div>
                        <p className="text-sm text-red-400">
                          {item.currentStock} left (Min: {item.minStock})
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-red-500 text-red-400 hover:bg-red-900/30 bg-transparent"
                      >
                        Restock
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
