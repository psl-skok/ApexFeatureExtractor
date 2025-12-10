'use client';

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Home, Upload, Share2, BarChart3 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-blue-100 flex flex-col items-center px-8 py-10 text-gray-900">
      
      {/* Header */}
      <div className="w-full max-w-6xl bg-blue-200 rounded-2xl shadow-sm p-6 flex items-center justify-between border border-blue-300">
        <div className="flex items-center gap-3">
          <div className="bg-white p-3 rounded-xl shadow-sm">
            <Home className="text-blue-600" size={28} />
          </div>
          <h1 className="text-4xl font-extrabold text-gray-800">
            Apex Feature Extractor
          </h1>
        </div>
        <div className="bg-white rounded-xl px-4 py-2 shadow-sm">
            <a
              href="https://apexstrategyadvisors.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Image
                src="/apex-logo.png"
                alt="Apex logo"
                width={140}
                height={140}
                className="object-contain cursor-pointer"
              />
            </a>
        </div>
      </div>

      {/* Subtitle */}
      <p className="text-center mt-2 text-gray-700 text-lg font-medium">
        AI-Powered Sales Call Analysis & Feature Extraction Tool
      </p>

      {/* Welcome Section */}
      <div className="mt-10 w-full max-w-6xl bg-blue-200 border border-blue-300 rounded-2xl shadow-sm text-center py-10 px-6">
        <h2 className="text-3xl font-extrabold mb-4 text-gray-900">
          Welcome to Apex Feature Extractor
        </h2>
        <p className="text-lg text-gray-700 mb-6 max-w-2xl mx-auto">
          Upload your data, build analytical pipelines, and visualize call insights — all in one place.
        </p>
        <Button
          asChild
          variant="outline"
          className="border-2 border-blue-400 hover:bg-blue-300 text-gray-900 text-lg px-6 py-2"
        >
          <Link href="/data-input">Get Started</Link>
        </Button>
      </div>

      {/* Three Main Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10 w-full max-w-6xl">
        <Link href="/data-input">
          <Card className="bg-blue-100 border border-blue-300 hover:bg-blue-200 transition-all duration-200">
            <CardContent className="flex flex-col items-center p-6">
              <Upload size={50} className="mb-4 text-gray-800" />
              <h3 className="text-xl font-bold underline mb-2">Data Input</h3>
              <p className="text-gray-700 text-center">
                Upload CSVs and preview data
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/graph-edit">
          <Card className="bg-blue-100 border border-blue-300 hover:bg-blue-200 transition-all duration-200">
            <CardContent className="flex flex-col items-center p-6">
              <Share2 size={50} className="mb-4 text-gray-800" />
              <h3 className="text-xl font-bold underline mb-2">Graph Edit</h3>
              <p className="text-gray-700 text-center">
                Chain functions and tune analysis
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/insight-visualizer"> 
          <Card className="bg-blue-100 border border-blue-300 hover:bg-blue-200 transition-all duration-200">
            <CardContent className="flex flex-col items-center p-6">
              <BarChart3 size={50} className="mb-4 text-gray-800" />
              <h3 className="text-xl font-bold underline mb-2">Insight Visualizer</h3>
              <p className="text-gray-700 text-center">
                View insights, export results
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </main>
  );
}
