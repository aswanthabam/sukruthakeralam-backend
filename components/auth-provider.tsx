"use client"

import type React from "react"

import { createContext, useContext, useEffect, useState } from "react"
import { useRouter } from "next/navigation"

interface AuthContextType {
  isAuthenticated: boolean
  userEmail: string | null
  login: (email: string, token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    const authStatus = localStorage.getItem("isAuthenticated") === "true"
    const email = localStorage.getItem("userEmail")

    // Only consider authenticated if both token and auth status exist
    const isAuth = authStatus && token
    setIsAuthenticated(!!isAuth)
    setUserEmail(email)
    setIsLoading(false)

    // Set cookie for middleware
    if (isAuth) {
      document.cookie = "isAuthenticated=true; path=/"
    }
  }, [])

  const login = (email: string, token: string) => {
    localStorage.setItem("access_token", token)
    localStorage.setItem("isAuthenticated", "true")
    localStorage.setItem("userEmail", email)
    document.cookie = "isAuthenticated=true; path=/"
    setIsAuthenticated(true)
    setUserEmail(email)
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("isAuthenticated")
    localStorage.removeItem("userEmail")
    document.cookie = "isAuthenticated=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT"
    setIsAuthenticated(false)
    setUserEmail(null)
    router.push("/login")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return <AuthContext.Provider value={{ isAuthenticated, userEmail, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
