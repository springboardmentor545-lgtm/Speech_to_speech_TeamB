import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Mic, Globe } from "lucide-react";

const navigation = [
  { name: "Milestone 1: Transcription", href: "/milestone1", icon: Mic, color: "text-blue-400" },
  { name: "Milestone 2: Translation", href: "/milestone2", icon: Globe, color: "text-green-400" },
];

export default function Layout() {
  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <div className="hidden md:flex md:flex-col md:w-64 bg-gray-800 border-r border-gray-700">
        <div className="flex items-center px-4 py-5 space-x-3">
          <svg className="w-8 h-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
          <span className="text-lg font-bold text-white">AI Speech Platform</span>
        </div>

        <nav className="mt-4 flex-1 px-3 space-y-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `group flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-all duration-300
                 ${
                   isActive
                     ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg scale-[1.03]"
                     : "text-gray-300 hover:text-white hover:bg-white/10"
                 }`
              }
            >
              <item.icon className={`mr-3 h-6 w-6 transition-colors duration-300 ${item.color}`} />
              {item.name}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex flex-col flex-1 overflow-y-auto">
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet /> {/* ⬅️ renders Milestone1 / Milestone2 */}
          </div>
        </main>
      </div>
    </div>
  );
}
