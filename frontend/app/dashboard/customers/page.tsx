"use client"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Search, User, Phone, MapPin, Eye } from "lucide-react"

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([])
  const [orders, setOrders] = useState<any[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCustomer, setSelectedCustomer] = useState<any | null>(null)
  const [customerOrders, setCustomerOrders] = useState<any[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const user = JSON.parse(localStorage.getItem("user") || '{}')

  useEffect(() => {
    async function fetchCustomersAndOrders() {
      if (!user.token) return
      
      try {
        const customersRes = await fetch('http://localhost:5000/api/customers', {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'Content-Type': 'application/json'
          }
        })
        const customersData = await customersRes.json()
        if (customersData.success) setCustomers(customersData.data)
        
        const ordersRes = await fetch('http://localhost:5000/api/orders', {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'Content-Type': 'application/json'
          }
        })
        const ordersData = await ordersRes.json()
        if (ordersData.success) setOrders(ordersData.data)
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }
    fetchCustomersAndOrders()
  }, [user.token])

  const filteredCustomers = customers.filter(
    (customer) =>
      customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.phone.includes(searchTerm) ||
      (customer.address && customer.address.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const handleViewOrders = (customer: any) => {
    setSelectedCustomer(customer)
    // Filter orders by customer_id or customer_phone
    const customerOrders = orders.filter((order) => 
      order.customer_id === customer.customer_id || 
      order.customer_phone === customer.phone
    )
    setCustomerOrders(customerOrders)
    setIsDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Customers</h1>
        <p className="text-muted-foreground mt-2">View all your customers and their orders</p>
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="Search customers by name, phone, or address..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCustomers.map((customer) => (
          <Card key={customer.customer_id || customer.phone} className="relative">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <User className="h-4 w-4" /> {customer.name}
                  </CardTitle>
                  <div className="text-sm text-muted-foreground flex items-center gap-2">
                    <span className="font-semibold">ID: {customer.customer_id}</span>
                  </div>
                  <div className="text-sm text-muted-foreground flex items-center gap-2">
                    <Phone className="h-4 w-4" /> {customer.phone}
                  </div>
                  <div className="text-sm text-muted-foreground flex items-center gap-2">
                    <MapPin className="h-4 w-4" /> {customer.address}
                  </div>
                </div>
                <Dialog open={isDialogOpen && selectedCustomer?.phone === customer.phone} onOpenChange={setIsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" onClick={() => handleViewOrders(customer)}>
                      <Eye className="h-4 w-4 mr-1" /> View Orders
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Orders for {customer.name}</DialogTitle>
                    </DialogHeader>
                    {customerOrders.length === 0 ? (
                      <div className="text-center text-muted-foreground py-8">No orders found for this customer.</div>
                    ) : (
                      <div className="space-y-4">
                        {customerOrders.map((order) => (
                          <Card key={order.order_id}>
                            <CardContent className="p-4">
                              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                                <div>
                                  <div className="font-semibold">Order ID: {order.order_id}</div>
                                  <div className="text-sm text-muted-foreground">Customer ID: {order.customer_id}</div>
                                  <div className="text-sm text-muted-foreground">Status: {order.status}</div>
                                  <div className="text-sm text-muted-foreground">Total: ₹{order.total}</div>
                                  <div className="text-sm text-muted-foreground">Date: {new Date(order.timestamp).toLocaleString()}</div>
                                </div>
                                <div>
                                  <div className="font-semibold mb-1">Items:</div>
                                  <ul className="list-disc list-inside text-sm">
                                    {order.items.map((item: any, idx: number) => (
                                      <li key={idx}>{item.name} ({item.quantity})</li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
                              {order.notes && (
                                <div className="mt-2 text-xs text-blue-600">Notes: {order.notes}</div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
      {filteredCustomers.length === 0 && (
        <div className="text-center py-12">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No customers found</h3>
          <p className="text-muted-foreground">
            {searchTerm ? "Try adjusting your search terms" : "You have no customers yet."}
          </p>
        </div>
      )}
    </div>
  )
} 