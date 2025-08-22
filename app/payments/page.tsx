"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Filter, Download, Eye, Edit, ArrowUpDown } from "lucide-react"
import { DateRangePicker } from "@/components/date-range-picker"
import { LogoutButton } from "@/components/logout-button"
import type { DateRange } from "react-day-picker"
import Link from "next/link"

// Mock data for payments
const paymentsData = [
  {
    id: 1,
    name: "Rajesh Kumar",
    phone: "+91 9876543210",
    email: "rajesh.kumar@email.com",
    amount: 2500,
    status: "Completed",
    date: "2024-01-15",
    paymentMethod: "UPI",
  },
  {
    id: 2,
    name: "Priya Nair",
    phone: "+91 9876543211",
    email: "priya.nair@email.com",
    amount: 1800,
    status: "Pending",
    date: "2024-01-14",
    paymentMethod: "Bank Transfer",
  },
  {
    id: 3,
    name: "Suresh Menon",
    phone: "+91 9876543212",
    email: "suresh.menon@email.com",
    amount: 3200,
    status: "Completed",
    date: "2024-01-13",
    paymentMethod: "Cash",
  },
  {
    id: 4,
    name: "Anitha Pillai",
    phone: "+91 9876543213",
    email: "anitha.pillai@email.com",
    amount: 1500,
    status: "Failed",
    date: "2024-01-12",
    paymentMethod: "UPI",
  },
  {
    id: 5,
    name: "Mohanan K",
    phone: "+91 9876543214",
    email: "mohanan.k@email.com",
    amount: 2200,
    status: "Completed",
    date: "2024-01-11",
    paymentMethod: "Bank Transfer",
  },
]

export default function PaymentsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sortField, setSortField] = useState("date")
  const [sortDirection, setSortDirection] = useState("desc")
  const [dateRange, setDateRange] = useState<DateRange | undefined>()

  const filteredPayments = paymentsData
    .filter((payment) => {
      const matchesSearch =
        payment.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        payment.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        payment.phone.includes(searchTerm)
      const matchesStatus = statusFilter === "all" || payment.status.toLowerCase() === statusFilter

      let matchesDate = true
      if (dateRange?.from) {
        const paymentDate = new Date(payment.date)
        const fromDate = dateRange.from
        const toDate = dateRange.to || dateRange.from
        matchesDate = paymentDate >= fromDate && paymentDate <= toDate
      }

      return matchesSearch && matchesStatus && matchesDate
    })
    .sort((a, b) => {
      const aValue = a[sortField as keyof typeof a]
      const bValue = b[sortField as keyof typeof b]
      const direction = sortDirection === "asc" ? 1 : -1
      return aValue > bValue ? direction : -direction
    })

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "bg-green-100 text-green-800 hover:bg-green-100"
      case "pending":
        return "bg-yellow-100 text-yellow-800 hover:bg-yellow-100"
      case "failed":
        return "bg-red-100 text-red-800 hover:bg-red-100"
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-100"
    }
  }

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Sukrutha Keralam</h1>
            <p className="text-sm text-muted-foreground">Payments Management</p>
          </div>
          <div className="flex items-center gap-4">
            <DateRangePicker dateRange={dateRange} onDateRangeChange={setDateRange} />
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <LogoutButton />
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-border bg-card">
        <div className="flex items-center px-6 py-3 space-x-6">
          <Link href="/" className="text-sm font-medium text-muted-foreground hover:text-foreground">
            Dashboard
          </Link>
          <Link href="/payments" className="text-sm font-medium text-accent hover:text-accent/80">
            Payments
          </Link>
          <Link href="/form-requests" className="text-sm font-medium text-muted-foreground hover:text-foreground">
            Form 80 Requests
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="p-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-semibold">Payment Records</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {dateRange?.from
                    ? `Showing payments from ${dateRange.from.toLocaleDateString()}${dateRange.to ? ` to ${dateRange.to.toLocaleDateString()}` : ""}`
                    : "Showing all payments"}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name, email, or phone..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 w-80"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <Filter className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("name")}>
                      <div className="flex items-center gap-2">
                        Name
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead>Phone Number</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("amount")}>
                      <div className="flex items-center gap-2">
                        Amount
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead>Payment Status</TableHead>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("date")}>
                      <div className="flex items-center gap-2">
                        Date
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead>Payment Method</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPayments.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell className="font-medium">{payment.name}</TableCell>
                      <TableCell>{payment.phone}</TableCell>
                      <TableCell>{payment.email}</TableCell>
                      <TableCell className="font-semibold">₹{payment.amount.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(payment.status)}>{payment.status}</Badge>
                      </TableCell>
                      <TableCell>{new Date(payment.date).toLocaleDateString()}</TableCell>
                      <TableCell>{payment.paymentMethod}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Showing {filteredPayments.length} of {paymentsData.length} payments
              </p>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" disabled>
                  Previous
                </Button>
                <Button variant="outline" size="sm" disabled>
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
