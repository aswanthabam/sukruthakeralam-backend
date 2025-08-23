import { DashboardContent } from "@/components/dashboard-content"
import { LogoutButton } from "@/components/logout-button"
import Link from "next/link"

export default function AdminDashboard() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Sukrutha Keralam</h1>
            <p className="text-sm text-muted-foreground">Admin Dashboard</p>
          </div>
          <LogoutButton />
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-border bg-card">
        <div className="flex items-center px-6 py-3 space-x-6">
          <Link href="/" className="text-sm font-medium text-primary font-semibold">
            Dashboard
          </Link>
          <Link href="/payments" className="text-sm font-medium text-muted-foreground hover:text-foreground">
            Payments
          </Link>
          <Link href="/form-requests" className="text-sm font-medium text-muted-foreground hover:text-foreground">
            Form 80 Requests
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <DashboardContent />
    </div>
  )
}
