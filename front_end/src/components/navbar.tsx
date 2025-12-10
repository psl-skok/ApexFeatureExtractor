"use client"

import Image from "next/image"
import Link from "next/link"
import { Home } from "lucide-react"

export default function Navbar() {
  return (
    <header className="flex justify-between items-center w-full bg-blue-100 px-6 py-4 rounded-b-2xl shadow-sm">
      {/* Left: Home icon + title */}
      <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition">
        <Home className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-900">Apex Feature Extractor</h1>
      </Link>

      {/* Right: Apex logo */}
      <div className="flex items-center">
        <Image
          src="/apex-logo.png"
          alt="Apex logo"
          width={100}
          height={100}
          className="rounded-lg object-contain"
        />
      </div>
    </header>
  )
}
