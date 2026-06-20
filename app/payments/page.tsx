"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Search,
  Filter,
  Eye,
  Edit,
  ArrowUpDown,
  Loader2,
  RefreshCw,
  RefreshCcw,
} from "lucide-react";
import { DateRangePicker } from "@/components/date-range-picker";
import { LogoutButton } from "@/components/logout-button";
import { axiosInstance } from "@/lib/axios";
import type { DateRange } from "react-day-picker";
import Link from "next/link";

interface Donation {
  id: string; // Added id field for donation details API
  order_id: string;
  full_name: string;
  email: string;
  amount: number;
  status: string;
  need_g80_certificate: boolean;
  created_at: string;
}

interface DonationDetails {
  order_id: string;
  full_name: string;
  email: string;
  contact_number: string;
  amount: number;
  status: string;
  need_g80_certificate: boolean;
  g80_certificate_id?: string;
  payment_details:
    | {
        gateway: "phonepe";
        payment_status: string;
        merchant_order_id: string;
        phonepe_order_id: string;
        payment_mode?: string | null;
        redirect_url?: string | null;
      }
    | {
        gateway: "sbiepay";
        payment_status: string;
        merchant_order_id: string;
        sbiepay_ref_id?: string | null;
        pay_mode?: string | null;
        bank_code?: string | null;
        bank_reference_number?: string | null;
        transaction_date?: string | null;
        reason_message?: string | null;
      };
  donation: {
    full_name: string;
    contact_number: string;
    need_g80_certificate: boolean;
    confirmed_terms: boolean;
    is_deleted: boolean;
    email: string;
    id: string;
    order_id: string;
    amount: number;
    status: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;
    g80_certificate?: {
      pan_number: string;
      id: string;
      city: string;
      country: string;
      status: string;
      is_deleted: boolean;
      donation_id: string;
      full_address: string;
      state: string;
      pin_code: string;
      created_at: string;
      updated_at: string;
      deleted_at: string | null;
    };
  };
}

export default function PaymentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("completed"); // Set default status filter to "completed"
  const [sortField, setSortField] = useState("created_at");
  const [sortDirection, setSortDirection] = useState("desc");
  const [dateRange, setDateRange] = useState<DateRange | undefined>();
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    limit: 10,
    offset: 0,
    next: null as string | null,
    previous: null as string | null,
    total: 0,
  });

  const [selectedDonation, setSelectedDonation] =
    useState<DonationDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [refreshDisabled, setRefreshDisabled] = useState(false);

  const fetchDonations = useCallback(
    async (offset = 0) => {
      try {
        setLoading(true);
        const params: any = {
          limit: 10,
          offset,
        };

        // Add search parameter
        if (searchTerm.trim()) {
          params.search = searchTerm.trim();
        }

        // Add status filter parameter
        if (statusFilter !== "all") {
          params.status = statusFilter;
        }

        // Add date filtering if date range is selected
        if (dateRange?.from) {
          const fromDate = new Date(dateRange.from);
          fromDate.setHours(0, 0, 0, 0);
          params.from_datetime = fromDate.toISOString();

          if (dateRange.to) {
            const toDate = new Date(dateRange.to);
            toDate.setHours(23, 59, 59, 999);
            params.to_datetime = toDate.toISOString();
          } else {
            const toDate = new Date(dateRange.from);
            toDate.setHours(23, 59, 59, 999);
            params.to_datetime = toDate.toISOString();
          }
        }

        const response = await axiosInstance.get(
          "/api/donation/list_donations",
          { params }
        );
        const responseData = response.data;

        // Handle both paginated response structure and direct array
        const donationsArray = responseData.items || responseData || [];
        setDonations(Array.isArray(donationsArray) ? donationsArray : []);

        setPagination({
          limit: responseData.limit || 10,
          offset: responseData.offset || offset,
          next: responseData.next || null,
          previous: responseData.previous || null,
          total: responseData.total || donationsArray.length,
        });
      } catch (error) {
        console.error("Error fetching donations:", error);
        setDonations([]);
      } finally {
        setLoading(false);
      }
    },
    [searchTerm, statusFilter, dateRange]
  );

  useEffect(() => {
    fetchDonations(0);
  }, [fetchDonations]);

  const displayedDonations = donations;

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "bg-green-100 text-green-800 hover:bg-green-100";
      case "pending":
        return "bg-yellow-100 text-yellow-800 hover:bg-yellow-100";
      case "payment_failed":
        return "bg-red-100 text-red-800 hover:bg-red-100";
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-100";
    }
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handlePrevious = () => {
    if (pagination.previous) {
      const newOffset = Math.max(0, pagination.offset - pagination.limit);
      fetchDonations(newOffset);
    }
  };

  const handleNext = () => {
    if (pagination.next) {
      const newOffset = pagination.offset + pagination.limit;
      fetchDonations(newOffset);
    }
  };

  const fetchDonationDetails = async (donationId: string) => {
    try {
      setDetailsLoading(true);
      const response = await axiosInstance.get<DonationDetails>(
        `/api/donation/donation-details/${donationId}`
      );
      setSelectedDonation(response.data);
      setShowDetailsDialog(true);
    } catch (error) {
      console.error("Error fetching donation details:", error);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchDonations(0);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              Sukrutha Keralam
            </h1>
            <p className="text-sm text-muted-foreground">Payments Management</p>
          </div>
          <div className="flex items-center gap-4">
            <DateRangePicker
              dateRange={dateRange}
              onDateRangeChange={setDateRange}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
            <LogoutButton />
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-border bg-card">
        <div className="flex items-center px-6 py-3 space-x-6">
          <Link
            href="/"
            className="text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Dashboard
          </Link>
          <Link
            href="/payments"
            className="text-sm font-medium text-primary font-semibold"
          >
            Payments
          </Link>
          <Link
            href="/form-requests"
            className="text-sm font-medium text-muted-foreground hover:text-foreground"
          >
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
                <CardTitle className="text-xl font-semibold">
                  Payment Records
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {dateRange?.from
                    ? `Showing payments from ${dateRange.from.toLocaleDateString()}${
                        dateRange.to
                          ? ` to ${dateRange.to.toLocaleDateString()}`
                          : ""
                      }`
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
                    <SelectItem value="payment_failed">Failed</SelectItem>
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
                        <TableHead
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => handleSort("full_name")}
                        >
                          <div className="flex items-center gap-2">
                            Name
                            <ArrowUpDown className="h-4 w-4" />
                          </div>
                        </TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => handleSort("amount")}
                        >
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
                      {displayedDonations.map((donation) => (
                        <TableRow key={donation.order_id}>
                          <TableCell className="font-mono text-sm">
                            {donation.order_id}
                          </TableCell>
                          <TableCell className="font-medium">
                            {donation.full_name}
                          </TableCell>
                          <TableCell>{donation.email}</TableCell>
                          <TableCell className="font-semibold">
                            ₹{donation.amount.toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Badge className={getStatusColor(donation.status)}>
                              {donation.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                donation.need_g80_certificate
                                  ? "default"
                                  : "secondary"
                              }
                            >
                              {donation.need_g80_certificate ? "Yes" : "No"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {new Date(donation.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  fetchDonationDetails(donation.id)
                                }
                                disabled={detailsLoading}
                              >
                                {detailsLoading ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Eye className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={
                                  donation.status == "completed" ||
                                  refreshDisabled
                                }
                                onClick={async () => {
                                  setRefreshDisabled(true);
                                  axiosInstance
                                    .get(
                                      "/api/donation/status/" +
                                        donation.order_id
                                    )
                                    .then((res) => {
                                      fetchDonations(pagination.offset);
                                      setRefreshDisabled(false);
                                    })
                                    .catch((err) => {
                                      setRefreshDisabled(false);
                                    });
                                }}
                              >
                                <RefreshCcw className="h-4 w-4" />
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
                    Showing {displayedDonations.length} payments (Offset:{" "}
                    {pagination.offset})
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handlePrevious}
                      disabled={!pagination.previous}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleNext}
                      disabled={!pagination.next}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
          <DialogContent
            style={{
              width: "90vw",
              maxWidth: "none",
              height: "90vh",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <DialogHeader>
              <DialogTitle>Donation Details</DialogTitle>
            </DialogHeader>
            {selectedDonation && (
              <div className="space-y-6">
                {/* Basic Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">
                    Basic Information
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="font-medium">Order ID:</span>
                        <span className="font-mono text-sm">
                          {selectedDonation.order_id}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Full Name:</span>
                        <span>{selectedDonation.full_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Email:</span>
                        <span className="break-all">
                          {selectedDonation.email}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Contact:</span>
                        <span className="break-all">
                          {selectedDonation.contact_number}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="font-medium">Amount:</span>
                        <span className="font-semibold">
                          ₹{selectedDonation.amount.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Status:</span>
                        <Badge
                          className={getStatusColor(selectedDonation.status)}
                        >
                          {selectedDonation.status}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Form 80 Required:</span>
                        <Badge
                          variant={
                            selectedDonation.need_g80_certificate
                              ? "default"
                              : "secondary"
                          }
                        >
                          {selectedDonation.need_g80_certificate ? "Yes" : "No"}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Created:</span>
                        <span>
                          {new Date(
                            selectedDonation.donation.created_at
                          ).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Payment Details */}
                {selectedDonation.payment_details.gateway == "phonepe" ? (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">
                      Payment Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="font-medium">Payment Status:</span>
                          <Badge
                            className={getStatusColor(
                              selectedDonation.payment_details.payment_status
                            )}
                          >
                            {selectedDonation.payment_details.payment_status}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Payment Mode:</span>
                          <span className="break-all">
                            {selectedDonation.payment_details.payment_mode}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="font-medium">
                            Merchant Order ID:
                          </span>
                          <span className="font-mono text-sm break-all">
                            {selectedDonation.payment_details.merchant_order_id}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">PhonePe Order ID:</span>
                          <span className="font-mono text-sm break-all">
                            {selectedDonation.payment_details.phonepe_order_id}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : selectedDonation.payment_details.gateway == "sbiepay" ? (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">
                      Payment Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="font-medium">Payment Status:</span>
                          <Badge
                            className={getStatusColor(
                              selectedDonation.payment_details.payment_status
                            )}
                          >
                            {selectedDonation.payment_details.payment_status}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Pay Mode:</span>
                          <span className="break-all">
                            {selectedDonation.payment_details.pay_mode}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Bank Code:</span>
                          <span className="break-all">
                            {selectedDonation.payment_details.bank_code}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Reason Message:</span>
                          <span className="break-all">
                            {selectedDonation.payment_details.reason_message}
                          </span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="font-medium">
                            Merchant Order ID:
                          </span>
                          <span className="font-mono text-sm break-all">
                            {selectedDonation.payment_details.merchant_order_id}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">SBIePay Ref ID:</span>
                          <span className="font-mono text-sm break-all">
                            {selectedDonation.payment_details.sbiepay_ref_id}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">
                            Bank Reference No.:
                          </span>
                          <span className="font-mono text-sm break-all">
                            {
                              selectedDonation.payment_details
                                .bank_reference_number
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Transaction Date:</span>
                          <span className="font-mono text-sm break-all">
                            {selectedDonation.payment_details.transaction_date}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <></>
                )}

                {/* G80 Certificate Details */}
                {selectedDonation.donation.g80_certificate && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">
                      Form 80 Certificate Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="font-medium">PAN Number:</span>
                          <span className="font-mono">
                            {
                              selectedDonation.donation.g80_certificate
                                .pan_number
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Status:</span>
                          <Badge
                            variant={
                              selectedDonation.donation.g80_certificate
                                .status === "pending"
                                ? "secondary"
                                : "default"
                            }
                          >
                            {selectedDonation.donation.g80_certificate.status}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">City:</span>
                          <span>
                            {selectedDonation.donation.g80_certificate.city}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">State:</span>
                          <span>
                            {selectedDonation.donation.g80_certificate.state}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="font-medium">Country:</span>
                          <span>
                            {selectedDonation.donation.g80_certificate.country}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Pin Code:</span>
                          <span>
                            {selectedDonation.donation.g80_certificate.pin_code}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Address:</span>
                          <span className="text-right max-w-xs">
                            {
                              selectedDonation.donation.g80_certificate
                                .full_address
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="font-medium">Requested:</span>
                          <span>
                            {new Date(
                              selectedDonation.donation.g80_certificate.created_at
                            ).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
