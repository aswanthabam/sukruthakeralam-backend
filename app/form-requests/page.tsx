"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Search, Filter, Download, Eye, ArrowUpDown, CheckCircle, Clock, Edit2 } from "lucide-react"
import { DateRangePicker } from "@/components/date-range-picker"
import { LogoutButton } from "@/components/logout-button"
import { axiosInstance } from "@/lib/axios"
import type { DateRange } from "react-day-picker"
import Link from "next/link"

interface Form80Request {
  id: string
  donation: {
    id: string
    order_id: string
    full_name: string
    email: string
    amount: number
    status: string
    need_g80_certificate: boolean
    created_at: string
  }
  pan_number: string
  full_address: string
  city: string
  state: string
  country: string
  pin_code: string
  status: "pending" | "given"
  created_at: string
}

interface ApiResponse {
  limit: number
  offset: number
  next: string | null
  previous: string | null
  items: Form80Request[]
}

export default function FormRequestsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sortField, setSortField] = useState("created_at")
  const [sortDirection, setSortDirection] = useState("desc")
  const [requests, setRequests] = useState<Form80Request[]>([])
  const [dateRange, setDateRange] = useState<DateRange | undefined>()
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({
    limit: 10,
    offset: 0,
    next: null as string | null,
    previous: null as string | null,
  })
  const [selectedRequest, setSelectedRequest] = useState<Form80Request | null>(null)
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false)
  const [viewRequest, setViewRequest] = useState<Form80Request | null>(null)

  const fetchRequests = useCallback(
    async (offset = 0) => {
      try {
        setLoading(true)
        const params: any = {
          limit: 10,
          offset,
        }

        // Add search parameter
        if (searchTerm.trim()) {
          params.search = searchTerm.trim()
        }

        // Add status filter parameter
        if (statusFilter !== "all") {
          params.status = statusFilter
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

        const response = await axiosInstance.get<ApiResponse>("/api/donation/list_form80_requests", { params })
        setRequests(response.data.items)
        setPagination({
          limit: response.data.limit,
          offset: response.data.offset,
          next: response.data.next,
          previous: response.data.previous,
        })
      } catch (error) {
        console.error("Error fetching form80 requests:", error)
      } finally {
        setLoading(false)
      }
    },
    [searchTerm, statusFilter, dateRange],
  )

  const updateRequestStatus = async (requestId: string, newStatus: "pending" | "given") => {
    try {
      setStatusUpdateLoading(true)
      await axiosInstance.post(`/api/donation/submit_form80/${requestId}`, {
        status: newStatus,
      })

      // Update local state
      setRequests((prev) =>
        prev.map((request) => (request.id === requestId ? { ...request, status: newStatus } : request)),
      )
      setIsDialogOpen(false)
      setSelectedRequest(null)
    } catch (error) {
      console.error("Error updating form80 status:", error)
    } finally {
      setStatusUpdateLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests(0)
  }, [fetchRequests])

  const displayedRequests = requests

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

  const handlePrevious = () => {
    if (pagination.previous) {
      const newOffset = Math.max(0, pagination.offset - pagination.limit)
      fetchRequests(newOffset)
    }
  }

  const handleNext = () => {
    if (pagination.next) {
      const newOffset = pagination.offset + pagination.limit
      fetchRequests(newOffset)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading form requests...</p>
        </div>
      </div>
    )
  }

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
          <Link href="/form-requests" className="text-sm font-medium text-primary font-semibold">
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
                    <TableHead>Order ID</TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort("donation.full_name")}
                    >
                      <div className="flex items-center gap-2">
                        Name
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>PAN Number</TableHead>
                    <TableHead>Address</TableHead>
                    <TableHead>Form Status</TableHead>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("created_at")}>
                      <div className="flex items-center gap-2">
                        Request Date
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayedRequests.map((request) => (
                    <TableRow key={request.id}>
                      <TableCell className="font-mono text-sm">{request.donation.order_id}</TableCell>
                      <TableCell className="font-medium">{request.donation.full_name}</TableCell>
                      <TableCell>{request.donation.email}</TableCell>
                      <TableCell className="font-semibold">₹{request.donation.amount.toLocaleString()}</TableCell>
                      <TableCell className="font-mono text-sm">{request.pan_number}</TableCell>
                      <TableCell
                        className="max-w-xs truncate"
                        title={`${request.full_address}, ${request.city}, ${request.state}, ${request.country} - ${request.pin_code}`}
                      >
                        {request.city}, {request.state}
                      </TableCell>
                      <TableCell>
                        <Badge className={`${getStatusColor(request.status)} flex items-center gap-1 w-fit`}>
                          {getStatusIcon(request.status)}
                          {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(request.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Dialog
                            open={isViewDialogOpen && viewRequest?.id === request.id}
                            onOpenChange={(open) => {
                              setIsViewDialogOpen(open)
                              if (!open) setViewRequest(null)
                            }}
                          >
                            <DialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setViewRequest(request)}
                                title="View Details"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>Form 80 Request Details</DialogTitle>
                                <DialogDescription>
                                  Complete details for {request.donation.full_name}'s Form 80 request.
                                </DialogDescription>
                              </DialogHeader>
                              <div className="py-4">
                                <div className="grid grid-cols-2 gap-4">
                                  <div className="space-y-3">
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Order ID</label>
                                      <p className="font-mono text-sm">{request.donation.order_id}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Full Name</label>
                                      <p className="font-medium">{request.donation.full_name}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Email</label>
                                      <p>{request.donation.email}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Donation Amount
                                      </label>
                                      <p className="font-semibold">₹{request.donation.amount.toLocaleString()}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">PAN Number</label>
                                      <p className="font-mono text-sm">{request.pan_number}</p>
                                    </div>
                                  </div>
                                  <div className="space-y-3">
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Full Address</label>
                                      <p>{request.full_address}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">City</label>
                                      <p>{request.city}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">State</label>
                                      <p>{request.state}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Country</label>
                                      <p>{request.country}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">PIN Code</label>
                                      <p className="font-mono text-sm">{request.pin_code}</p>
                                    </div>
                                  </div>
                                </div>
                                <div className="mt-4 pt-4 border-t">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Form Status</label>
                                      <div className="mt-1">
                                        <Badge
                                          className={`${getStatusColor(request.status)} flex items-center gap-1 w-fit`}
                                        >
                                          {getStatusIcon(request.status)}
                                          {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                                        </Badge>
                                      </div>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">Request Date</label>
                                      <p>{new Date(request.created_at).toLocaleDateString()}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                              <DialogFooter>
                                <Button variant="outline" onClick={() => setIsViewDialogOpen(false)}>
                                  Close
                                </Button>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                          <Dialog
                            open={isDialogOpen && selectedRequest?.id === request.id}
                            onOpenChange={(open) => {
                              setIsDialogOpen(open)
                              if (!open) setSelectedRequest(null)
                            }}
                          >
                            <DialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedRequest(request)}
                                title="Update Status"
                              >
                                <Edit2 className="h-4 w-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Update Form 80 Status</DialogTitle>
                                <DialogDescription>
                                  Update the status for {request.donation.full_name}'s Form 80 request.
                                </DialogDescription>
                              </DialogHeader>
                              <div className="py-4">
                                <div className="space-y-2">
                                  <p>
                                    <strong>Order ID:</strong> {request.donation.order_id}
                                  </p>
                                  <p>
                                    <strong>Name:</strong> {request.donation.full_name}
                                  </p>
                                  <p>
                                    <strong>Amount:</strong> ₹{request.donation.amount.toLocaleString()}
                                  </p>
                                  <p>
                                    <strong>Current Status:</strong>
                                    <Badge className={`ml-2 ${getStatusColor(request.status)}`}>
                                      {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                                    </Badge>
                                  </p>
                                </div>
                              </div>
                              <DialogFooter>
                                <Button
                                  variant="outline"
                                  onClick={() => setIsDialogOpen(false)}
                                  disabled={statusUpdateLoading}
                                >
                                  Cancel
                                </Button>
                                {request.status === "pending" ? (
                                  <Button
                                    onClick={() => updateRequestStatus(request.id, "given")}
                                    disabled={statusUpdateLoading}
                                    className="bg-green-600 hover:bg-green-700"
                                  >
                                    {statusUpdateLoading ? "Updating..." : "Mark as Given"}
                                  </Button>
                                ) : (
                                  <Button
                                    onClick={() => updateRequestStatus(request.id, "pending")}
                                    disabled={statusUpdateLoading}
                                    variant="outline"
                                  >
                                    {statusUpdateLoading ? "Updating..." : "Mark as Pending"}
                                  </Button>
                                )}
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
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
                Showing {displayedRequests.length} requests (Offset: {pagination.offset})
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
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
