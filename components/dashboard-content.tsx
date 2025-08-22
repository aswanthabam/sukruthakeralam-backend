"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { CalendarDays, IndianRupee, Users, FileText, Filter } from "lucide-react"
import { StatsCard } from "@/components/stats-card"
import { DateRangePicker } from "@/components/date-range-picker"
import type { DateRange } from "react-day-picker"

// Mock data with dates
const mockPayments = [
  { name: "Rajesh Kumar", amount: 2500, status: "Completed", date: "2024-01-15" },
  { name: "Priya Nair", amount: 1800, status: "Pending", date: "2024-01-14" },
  { name: "Suresh Menon", amount: 3200, status: "Completed", date: "2024-01-13" },
  { name: "Anitha Pillai", amount: 1500, status: "Failed", date: "2024-01-12" },
  { name: "Mohanan K", amount: 2200, status: "Completed", date: "2024-01-11" },
]

const mockFormRequests = [
  { name: "Anitha Pillai", status: "Pending", date: "2024-01-15", amount: 500 },
  { name: "Mohanan K", status: "Given", date: "2024-01-13", amount: 500 },
  { name: "Lakshmi Devi", status: "Pending", date: "2024-01-12", amount: 500 },
]

export function DashboardContent() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>()

  const filterDataByDate = (data: any[], dateField: string) => {
    if (!dateRange?.from) return data

    return data.filter((item) => {
      const itemDate = new Date(item[dateField])
      const fromDate = dateRange.from!
      const toDate = dateRange.to || dateRange.from!

      return itemDate >= fromDate && itemDate <= toDate
    })
  }

  const filteredPayments = filterDataByDate(mockPayments, "date")
  const filteredFormRequests = filterDataByDate(mockFormRequests, "date")

  const totalCollected = filteredPayments.filter((p) => p.status === "Completed").reduce((sum, p) => sum + p.amount, 0)

  const todayCollected = filteredPayments
    .filter((p) => p.status === "Completed" && p.date === new Date().toISOString().split("T")[0])
    .reduce((sum, p) => sum + p.amount, 0)

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
          value={`₹${totalCollected.toLocaleString()}`}
          description={dateRange?.from ? "Filtered period" : "All time collections"}
          icon={IndianRupee}
          trend="+12.5%"
        />
        <StatsCard
          title="Today Collected"
          value={`₹${todayCollected.toLocaleString()}`}
          description="Today's collections"
          icon={CalendarDays}
          trend="+5.2%"
        />
        <StatsCard
          title="Total Payments"
          value={filteredPayments.length.toString()}
          description={dateRange?.from ? "Filtered period" : "All payment records"}
          icon={Users}
          trend="+8.1%"
        />
        <StatsCard
          title="Form 80 Requests"
          value={filteredFormRequests.length.toString()}
          description={`Pending: ${filteredFormRequests.filter((r) => r.status === "Pending").length}, Given: ${filteredFormRequests.filter((r) => r.status === "Given").length}`}
          icon={FileText}
          trend="+3.4%"
        />
      </div>
    </main>
  )
}
