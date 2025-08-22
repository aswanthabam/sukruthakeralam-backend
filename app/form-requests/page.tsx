"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Filter, Download, Eye, Edit, ArrowUpDown, CheckCircle, Clock } from "lucide-react"
import { DateRangePicker } from "@/components/date-range-picker"
import { LogoutButton } from "@/components/logout-button"
import type { DateRange } from "react-day-picker"
import Link from "next/link"

// Mock data for Form 80 requests
const formRequestsData = [
  {
    id: 1,
    name: "Anitha Pillai",
    phone: "+91 9876543213",
    email: "anitha.pillai@email.com",
    amount: 500,
    status: "Pending",
    requestDate: "2024-01-15",
    completedDate: null,
  },
  {
    id: 2,
    name: "Mohanan K",
    phone: "+91 9876543214",
    email: "mohanan.k@email.com",
    amount: 500,
    status: "Given",
    requestDate: "2024-01-13",
    completedDate: "2024-01-14",
  },
  {
    id: 3,
    name: "Lakshmi Devi",
    phone: "+91 9876543215",
    email: "lakshmi.devi@email.com",
    amount: 500,
    status: "Pending",
    requestDate: "2024-01-12",
    completedDate: null,
  },
  {
    id: 4,
    name: "Ravi Varma",
    phone: "+91 9876543216",
    email: "ravi.varma@email.com",
    amount: 500,
    status: "Given",
    requestDate: "2024-01-10",
    completedDate: "2024-01-11",
  },
  {
    id: 5,
    name: "Sita Nair",
    phone: "+91 9876543217",
    email: "sita.nair@email.com",
    amount: 500,
    status: "Pending",
    requestDate: "2024-01-09",
    completedDate: null,
  },
  {
    id: 6,
    name: "Krishna Menon",
    phone: "+91 9876543218",
    email: "krishna.menon@email.com",
    amount: 500,
    status: "Given",
    requestDate: "2024-01-08",
    completedDate: "2024-01-09",
  },
]

export default function FormRequestsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sortField, setSortField] = useState("requestDate")
  const [sortDirection, setSortDirection] = useState("desc")
  const [requests, setRequests] = useState(formRequestsData)
  const [dateRange, setDateRange] = useState<DateRange | undefined>()

  const filteredRequests = requests
    .filter((request) => {
      const matchesSearch =
        request.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        request.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        request.phone.includes(searchTerm)
      const matchesStatus = statusFilter === "all" || request.status.toLowerCase() === statusFilter

      let matchesDate = true
      if (dateRange?.from) {
        const requestDate = new Date(request.requestDate)
        const fromDate = dateRange.from
        const toDate = dateRange.to || dateRange.from
        matchesDate = requestDate >= fromDate && requestDate <= toDate
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
      case "given":
        return "bg-green-100 text-green-800 hover:bg-green-100"
      case "pending":
        return "bg-orange-100 text-orange-800 hover:bg-orange-100"
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-100"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "given":
        return <CheckCircle className="h-4 w-4" />
      case "pending":
        return <Clock className="h-4 w-4" />
      default:
        return null
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

  const updateRequestStatus = (id: number, newStatus: string) => {
    setRequests((prev) =>
      prev.map((request) =>
        request.id === id
          ? {
              ...request,
              status: newStatus,
              completedDate: newStatus === "Given" ? new Date().toISOString().split("T")[0] : null,
            }
          : request,
      ),
    )
  }

  const pendingCount = filteredRequests.filter((r) => r.status === "Pending").length
  const givenCount = filteredRequests.filter((r) => r.status === "Given").length

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Sukrutha Keralam</h1>
            <p className="text-sm text-muted-foreground">Form 80 [G] Requests</p>
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
          <Link href="/payments" className="text-sm font-medium text-muted-foreground hover:text-foreground">
            Payments
          </Link>
          <Link href="/form-requests" className="text-sm font-medium text-accent hover:text-accent/80">
            Form 80 Requests
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="p-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Requests</p>
                  <p className="text-2xl font-bold text-foreground">{filteredRequests.length}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {dateRange?.from ? "Filtered period" : "All time"}
                  </p>
                </div>
                <div className="h-8 w-8 bg-accent/10 rounded-full flex items-center justify-center">
                  <Clock className="h-4 w-4 text-accent" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Pending</p>
                  <p className="text-2xl font-bold text-orange-600">{pendingCount}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {dateRange?.from ? "Filtered period" : "All time"}
                  </p>
                </div>
                <div className="h-8 w-8 bg-orange-100 rounded-full flex items-center justify-center">
                  <Clock className="h-4 w-4 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Given</p>
                  <p className="text-2xl font-bold text-green-600">{givenCount}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {dateRange?.from ? "Filtered period" : "All time"}
                  </p>
                </div>
                <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-semibold">Form 80 [G] Requests</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {dateRange?.from
                    ? `Showing requests from ${dateRange.from.toLocaleDateString()}${dateRange.to ? ` to ${dateRange.to.toLocaleDateString()}` : ""}`
                    : "Showing all requests"}
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
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="given">Given</SelectItem>
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
                    <TableHead>Amount</TableHead>
                    <TableHead>Form Status</TableHead>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("requestDate")}>
                      <div className="flex items-center gap-2">
                        Request Date
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead>Completed Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRequests.map((request) => (
                    <TableRow key={request.id}>
                      <TableCell className="font-medium">{request.name}</TableCell>
                      <TableCell>{request.phone}</TableCell>
                      <TableCell>{request.email}</TableCell>
                      <TableCell className="font-semibold">₹{request.amount}</TableCell>
                      <TableCell>
                        <Badge className={`${getStatusColor(request.status)} flex items-center gap-1 w-fit`}>
                          {getStatusIcon(request.status)}
                          {request.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(request.requestDate).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {request.completedDate ? new Date(request.completedDate).toLocaleDateString() : "-"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          {request.status === "Pending" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => updateRequestStatus(request.id, "Given")}
                              className="text-green-600 hover:text-green-700 hover:bg-green-50"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
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
                Showing {filteredRequests.length} of {requests.length} requests
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
