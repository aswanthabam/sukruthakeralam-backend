"use client"

import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"
import { useAuth } from "@/components/auth-provider"

export function LogoutButton() {
  const { logout, userEmail } = useAuth()

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-slate-600 hidden sm:inline">{userEmail}</span>
      <Button variant="outline" size="sm" onClick={logout} className="flex items-center gap-2 bg-transparent">
        <LogOut className="h-4 w-4" />
        <span className="hidden sm:inline">Logout</span>
      </Button>
    </div>
  )
}
