"use client"

import * as React from "react"
import { CalendarIcon } from "lucide-react"
import type { DateRange } from "react-day-picker"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface DateRangePickerProps {
  dateRange?: DateRange
  onDateRangeChange?: (dateRange: DateRange | undefined) => void
  placeholder?: string
  className?: string
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  placeholder = "Select date range",
  className,
}: DateRangePickerProps) {
  const [date, setDate] = React.useState<DateRange | undefined>(dateRange)

  const handleDateChange = (newDate: DateRange | undefined) => {
    setDate(newDate)
    onDateRangeChange?.(newDate)
  }

  const formatDateRange = (dateRange: DateRange | undefined) => {
    if (!dateRange?.from) return placeholder

    if (!dateRange.to) {
      return dateRange.from.toLocaleDateString()
    }

    return `${dateRange.from.toLocaleDateString()} - ${dateRange.to.toLocaleDateString()}`
  }

  const clearDateRange = () => {
    setDate(undefined)
    onDateRangeChange?.(undefined)
  }

  return (
    <div className={cn("grid gap-2", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant="outline"
            className={cn("w-[280px] justify-start text-left font-normal", !date && "text-muted-foreground")}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {formatDateRange(date)}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            initialFocus
            mode="range"
            defaultMonth={date?.from}
            selected={date}
            onSelect={handleDateChange}
            numberOfMonths={2}
          />
          <div className="p-3 border-t border-border">
            <div className="flex items-center justify-between gap-2">
              <Button variant="outline" size="sm" onClick={clearDateRange} className="flex-1 bg-transparent">
                Clear
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const today = new Date()
                  const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
                  handleDateChange({ from: lastWeek, to: today })
                }}
                className="flex-1"
              >
                Last 7 days
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const today = new Date()
                  const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
                  handleDateChange({ from: lastMonth, to: today })
                }}
                className="flex-1"
              >
                Last 30 days
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
