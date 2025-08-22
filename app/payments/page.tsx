"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Filter, Download, Eye, Edit, ArrowUpDown, Loader2 } from "lucide-react"
import { DateRangePicker } from "@/components/date-range-picker"
import { LogoutButton } from "@/components/logout-button"
import { axiosInstance } from "@/lib/axios"
import type { DateRange } from "react-day-picker"
import Link from "next/link"

interface Donation {
  order_id: string
  full_name: string
  email: string
  amount: number
  status: string
  need_g80_certificate: boolean
  created_at: string
}

interface DonationsResponse {
  limit: number
  offset: number
  next: string | null
  previous: string | null
  items: Donation[]
}

export default function PaymentsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sortField, setSortField] = useState("created_at")
  const [sortDirection, setSortDirection] = useState("desc")
  const [dateRange, setDateRange] = useState<DateRange | undefined>()
  const [donations, setDonations] = useState<Donation[]>([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({
    limit: 10,
    offset: 0,
    next: null as string | null,
    previous: null as string | null,
    total: 0,
  })

  const fetchDonations = async (offset = 0) => {
    try {
      setLoading(true)
      const params: any = {
        limit: 10,
        offset,
      }

      // Add date filtering if date range is selected
      if (dateRange?.from) {
        const fromDate = new Date(dateRange.from)
        fromDate.setHours(0, 0, 0, 0)
        params.from_datetime = fromDate.toISOString()

        if (dateRange.to) {
          const toDate = new Date(dateRange.to)
          toDate.setHours(23, 59, 59, 999)
          params.to_datetime = toDate.toISOString()
        } else {
          const toDate = new Date(dateRange.from)
          toDate.setHours(23, 59, 59, 999)
          params.to_datetime = toDate.toISOString()
        }
      }

      const response = await axiosInstance.get<DonationsResponse>("/api/donation/list_donations", { params })
      setDonations(response.data.items)
      setPagination({
        limit: response.data.limit,
        offset: response.data.offset,
        next: response.data.next,
        previous: response.data.previous,
        total: response.data.items.length,
      })
    } catch (error) {
      console.error("Error fetching donations:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDonations(0)
  }, [dateRange])

  const filteredDonations = donations
    .filter((donation) => {
      const matchesSearch =
        donation.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        donation.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        donation.order_id.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = statusFilter === "all" || donation.status.toLowerCase() === statusFilter

      return matchesSearch && matchesStatus
    })
    .sort((a, b) => {
      const aValue = a[sortField as keyof Donation]
      const bValue = b[sortField as keyof Donation]
      const direction = sortDirection === "asc" ? 1 : -1

      if (sortField === "amount") {
        return direction * (Number(aValue) - Number(bValue))
      }

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

  const handlePrevious = () => {
    if (pagination.previous) {
      const newOffset = Math.max(0, pagination.offset - pagination.limit)
      fetchDonations(newOffset)
    }
  }

  const handleNext = () => {
    if (pagination.next) {
      const newOffset = pagination.offset + pagination.limit
      fetchDonations(newOffset)
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
                    placeholder="Search by name, email, or order ID..."
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
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading payments...</span>
              </div>
            ) : (
              <>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Order ID</TableHead>
                        <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("full_name")}>
                          <div className="flex items-center gap-2">
                            Name
                            <ArrowUpDown className="h-4 w-4" />
                          </div>
                        </TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("amount")}>
                          <div className="flex items-center gap-2">
                            Amount
                            <ArrowUpDown className="h-4 w-4" />
                          </div>
                        </TableHead>
                        <TableHead>Payment Status</TableHead>
                        <TableHead>Form 80 Required</TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => handleSort("created_at")}
                        >
                          <div className="flex items-center gap-2">
                            Date
                            <ArrowUpDown className="h-4 w-4" />
                          </div>
                        </TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredDonations.map((donation) => (
                        <TableRow key={donation.order_id}>
                          <TableCell className="font-mono text-sm">{donation.order_id}</TableCell>
                          <TableCell className="font-medium">{donation.full_name}</TableCell>
                          <TableCell>{donation.email}</TableCell>
                          <TableCell className="font-semibold">₹{donation.amount.toLocaleString()}</TableCell>
                          <TableCell>
                            <Badge className={getStatusColor(donation.status)}>{donation.status}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={donation.need_g80_certificate ? "default" : "secondary"}>
                              {donation.need_g80_certificate ? "Yes" : "No"}
                            </Badge>
                          </TableCell>
                          <TableCell>{new Date(donation.created_at).toLocaleDateString()}</TableCell>
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
                    Showing {filteredDonations.length} payments (Offset: {pagination.offset})
                  </p>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handlePrevious} disabled={!pagination.previous}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleNext} disabled={!pagination.next}>
                      Next
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
