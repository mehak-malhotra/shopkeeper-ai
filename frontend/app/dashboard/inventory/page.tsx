"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { useToast } from "@/hooks/use-toast"
import { Plus, Search, Edit, Trash2, Package, AlertTriangle } from "lucide-react"

interface Product {
  id: string
  name: string
  price: number
  quantity: number
  minStock: number
  category: string
}

export default function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [newProduct, setNewProduct] = useState({
    name: "",
    price: "",
    quantity: "",
    minStock: "",
    category: "",
  })
  const { toast } = useToast()
  const user = JSON.parse(localStorage.getItem("user") || '{}')

  useEffect(() => {
    async function fetchInventory() {
      const res = await fetch(`http://localhost:5000/api/inventory?user_email=${encodeURIComponent(user.email)}`)
      const data = await res.json()
      if (data.success) setProducts(data.data)
    }
    if (user.email) fetchInventory()
  }, [user.email])

  const filteredProducts = products.filter(
    (product) =>
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.category.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const handleAddProduct = async () => {
    if (!newProduct.name || !newProduct.price || !newProduct.quantity) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }
    const product = {
      name: newProduct.name,
      price: Number.parseFloat(newProduct.price),
      quantity: Number.parseInt(newProduct.quantity),
      minStock: Number.parseInt(newProduct.minStock) || 5,
      category: newProduct.category || "General",
      user_email: user.email,
    }
    const res = await fetch("http://localhost:5000/api/inventory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(product),
    })
    const data = await res.json()
    if (data.success) {
      if (data.warning) {
        // Replace the existing product with the updated one (by name)
        setProducts((prev) => prev.map((p) => p.name === data.data.name ? data.data : p))
        toast({ title: "Product merged", description: data.warning, variant: "warning" })
      } else {
        setProducts((prev) => [...prev, data.data])
        toast({ title: "Product added", description: `${product.name} has been added to inventory` })
      }
    }
    setNewProduct({ name: "", price: "", quantity: "", minStock: "", category: "" })
    setIsAddDialogOpen(false)
  }

  const handleEditProduct = async () => {
    if (!editingProduct) return
    const res = await fetch(`http://localhost:5000/api/inventory/${editingProduct.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...editingProduct, user_email: user.email }),
    })
    const data = await res.json()
    if (data.success) setProducts((prev) => prev.map((p) => (p.id === editingProduct.id ? data.data : p)))
    setEditingProduct(null)
    setIsEditDialogOpen(false)
    toast({ title: "Product updated", description: `${editingProduct.name} has been updated` })
  }

  const handleDeleteProduct = async (productId: string) => {
    const res = await fetch(`http://localhost:5000/api/inventory/${productId}?user_email=${encodeURIComponent(user.email)}`, {
      method: "DELETE",
    })
    const data = await res.json()
    if (data.success) setProducts((prev) => prev.filter((p) => p.id !== productId))
    toast({ title: "Product deleted", description: `Product has been removed from inventory` })
  }

  const getStockStatus = (product: Product) => {
    if (product.quantity === 0) return { status: "Out of Stock", color: "bg-red-100 text-red-800" }
    if (product.quantity <= product.minStock) return { status: "Low Stock", color: "bg-yellow-100 text-yellow-800" }
    return { status: "In Stock", color: "bg-green-100 text-green-800" }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Inventory Management</h1>
          <p className="text-muted-foreground mt-2">Manage your products and stock levels</p>
        </div>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Product
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Product</DialogTitle>
              <DialogDescription>Add a new product to your inventory</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={newProduct.name}
                  onChange={(e) => setNewProduct((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter product name"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="category">Category</Label>
                <Input
                  id="category"
                  value={newProduct.category}
                  onChange={(e) => setNewProduct((prev) => ({ ...prev, category: e.target.value }))}
                  placeholder="Enter category"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="price">Price (₹) *</Label>
                  <Input
                    id="price"
                    type="number"
                    value={newProduct.price}
                    onChange={(e) => setNewProduct((prev) => ({ ...prev, price: e.target.value }))}
                    placeholder="0.00"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="quantity">Quantity *</Label>
                  <Input
                    id="quantity"
                    type="number"
                    value={newProduct.quantity}
                    onChange={(e) => setNewProduct((prev) => ({ ...prev, quantity: e.target.value }))}
                    placeholder="0"
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="minStock">Minimum Stock Level</Label>
                <Input
                  id="minStock"
                  type="number"
                  value={newProduct.minStock}
                  onChange={(e) => setNewProduct((prev) => ({ ...prev, minStock: e.target.value }))}
                  placeholder="5"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddProduct}>Add Product</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="Search products or categories..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{products.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock Items</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {products.filter((p) => p.quantity <= p.minStock && p.quantity > 0).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Out of Stock</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{products.filter((p) => p.quantity === 0).length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProducts.map((product) => {
          const stockStatus = getStockStatus(product)
          return (
            <Card key={product.id} className="relative">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{product.name}</CardTitle>
                    <CardDescription>{product.category}</CardDescription>
                  </div>
                  <Badge className={stockStatus.color}>{stockStatus.status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Price:</span>
                    <span className="font-semibold">₹{product.price}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Stock:</span>
                    <span
                      className={`font-semibold ${product.quantity <= product.minStock ? "text-red-600" : "text-green-600"}`}
                    >
                      {product.quantity} units
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Min Stock:</span>
                    <span className="text-sm">{product.minStock} units</span>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 bg-transparent"
                        onClick={() => setEditingProduct(product)}
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Product</DialogTitle>
                        <DialogDescription>Update product information</DialogDescription>
                      </DialogHeader>
                      {editingProduct && (
                        <div className="grid gap-4 py-4">
                          <div className="grid gap-2">
                            <Label htmlFor="edit-name">Product Name</Label>
                            <Input
                              id="edit-name"
                              value={editingProduct.name}
                              onChange={(e) =>
                                setEditingProduct((prev) => (prev ? { ...prev, name: e.target.value } : null))
                              }
                            />
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="edit-category">Category</Label>
                            <Input
                              id="edit-category"
                              value={editingProduct.category}
                              onChange={(e) =>
                                setEditingProduct((prev) => (prev ? { ...prev, category: e.target.value } : null))
                              }
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                              <Label htmlFor="edit-price">Price (₹)</Label>
                              <Input
                                id="edit-price"
                                type="number"
                                value={editingProduct.price}
                                onChange={(e) =>
                                  setEditingProduct((prev) =>
                                    prev ? { ...prev, price: Number.parseFloat(e.target.value) } : null,
                                  )
                                }
                              />
                            </div>
                            <div className="grid gap-2">
                              <Label htmlFor="edit-quantity">Quantity</Label>
                              <Input
                                id="edit-quantity"
                                type="number"
                                value={editingProduct.quantity}
                                onChange={(e) =>
                                  setEditingProduct((prev) =>
                                    prev ? { ...prev, quantity: Number.parseInt(e.target.value) } : null,
                                  )
                                }
                              />
                            </div>
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="edit-minStock">Minimum Stock Level</Label>
                            <Input
                              id="edit-minStock"
                              type="number"
                              value={editingProduct.minStock}
                              onChange={(e) =>
                                setEditingProduct((prev) =>
                                  prev ? { ...prev, minStock: Number.parseInt(e.target.value) } : null,
                                )
                              }
                            />
                          </div>
                        </div>
                      )}
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button onClick={handleEditProduct}>Update Product</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>

                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 bg-transparent">
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete Product</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to delete "{product.name}"? This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDeleteProduct(product.id)}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredProducts.length === 0 && (
        <div className="text-center py-12">
          <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No products found</h3>
          <p className="text-muted-foreground">
            {searchTerm ? "Try adjusting your search terms" : "Start by adding your first product"}
          </p>
        </div>
      )}
    </div>
  )
}
