"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { CalendarDays, IndianRupee, Users, FileText, Filter } from "lucide-react"
import { StatsCard } from "@/components/stats-card"
import { DateRangePicker } from "@/components/date-range-picker"
import { axiosInstance } from "@/lib/axios"
import type { DateRange } from "react-day-picker"

interface DonationTotalResponse {
  total_donation_amount: number
}

interface DonationCountResponse {
  total_donation_count: number
}

interface Form80RequestsResponse {
  total_form80_requests: number
}

export function DashboardContent() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>()
  const [totalCollected, setTotalCollected] = useState<number>(0)
  const [todayCollected, setTodayCollected] = useState<number>(0)
  const [totalDonations, setTotalDonations] = useState<number>(0)
  const [totalForm80Requests, setTotalForm80Requests] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)

  const getTodayDateRange = () => {
    const now = new Date()
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
    const endOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)

    return {
      from: startOfDay.toISOString(),
      to: endOfDay.toISOString(),
    }
  }

  const fetchTotalAmount = async (fromDate?: string, toDate?: string) => {
    try {
      const params: any = {}
      if (fromDate) params.from_datetime = fromDate
      if (toDate) params.to_datetime = toDate

      const response = await axiosInstance.get<DonationTotalResponse>("/api/donation/total_amount", { params })
      return response.data.total_donation_amount
    } catch (error) {
      console.error("Error fetching total amount:", error)
      return 0
    }
  }

  const fetchDonationCount = async (fromDate?: string, toDate?: string) => {
    try {
      const params: any = {}
      if (fromDate) params.from_datetime = fromDate
      if (toDate) params.to_datetime = toDate

      const response = await axiosInstance.get<DonationCountResponse>("/api/donation/total_count", { params })
      return response.data.total_donation_count
    } catch (error) {
      console.error("Error fetching donation count:", error)
      return 0
    }
  }

  const fetchForm80Requests = async (fromDate?: string, toDate?: string) => {
    try {
      const params: any = {}
      if (fromDate) params.from_datetime = fromDate
      if (toDate) params.to_datetime = toDate

      const response = await axiosInstance.get<Form80RequestsResponse>("/api/donation/total_form80_requests", {
        params,
      })
      return response.data.total_form80_requests
    } catch (error) {
      console.error("Error fetching form80 requests:", error)
      return 0
    }
  }

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)

      try {
        // Fetch total collected (filtered by date range if selected)
        const totalParams: any = {}
        if (dateRange?.from) {
          totalParams.from_datetime = dateRange.from.toISOString()
          if (dateRange.to) {
            totalParams.to_datetime = dateRange.to.toISOString()
          }
        }
        const total = await fetchTotalAmount(totalParams.from_datetime, totalParams.to_datetime)
        setTotalCollected(total)

        const donationCount = await fetchDonationCount(totalParams.from_datetime, totalParams.to_datetime)
        setTotalDonations(donationCount)

        const form80Count = await fetchForm80Requests(totalParams.from_datetime, totalParams.to_datetime)
        setTotalForm80Requests(form80Count)

        // Fetch today's collected amount
        const todayRange = getTodayDateRange()
        const todayTotal = await fetchTotalAmount(todayRange.from, todayRange.to)
        setTodayCollected(todayTotal)
      } catch (error) {
        console.error("Error fetching dashboard data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [dateRange])

  return (
    <main className="p-6">
      {/* Date Filter */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Overview</h2>
          <p className="text-sm text-muted-foreground">
            {dateRange?.from
              ? `Showing data from ${dateRange.from.toLocaleDateString()}${dateRange.to ? ` to ${dateRange.to.toLocaleDateString()}` : ""}`
              : "Showing all data"}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <DateRangePicker dateRange={dateRange} onDateRangeChange={setDateRange} />
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Total Collected"
          value={loading ? "Loading..." : `₹${totalCollected.toLocaleString()}`}
          description={dateRange?.from ? "Filtered period" : "All time collections"}
          icon={IndianRupee}
        />
        <StatsCard
          title="Today Collected"
          value={loading ? "Loading..." : `₹${todayCollected.toLocaleString()}`}
          description="Today's collections"
          icon={CalendarDays}
        />
        <StatsCard
          title="Total Payments"
          value={loading ? "Loading..." : totalDonations.toLocaleString()}
          description={dateRange?.from ? "Filtered period" : "All payment records"}
          icon={Users}
        />
        <StatsCard
          title="Form 80 Requests"
          value={loading ? "Loading..." : totalForm80Requests.toLocaleString()}
          description="Pending and given requests"
          icon={FileText}
        />
      </div>
    </main>
  )
}
