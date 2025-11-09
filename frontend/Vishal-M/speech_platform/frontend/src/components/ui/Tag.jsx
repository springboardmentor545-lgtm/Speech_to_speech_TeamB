// src/components/ui/Tag.jsx
import React from 'react';
export default function Tag({ children, color = 'blue' }) {
  const map = {
    blue: 'bg-blue-500/20 text-blue-300',
    green: 'bg-green-500/20 text-green-300',
    yellow: 'bg-yellow-500/20 text-yellow-300',
    pink: 'bg-pink-500/20 text-pink-300',
    purple: 'bg-purple-500/20 text-purple-300',
    gray: 'bg-gray-600/30 text-gray-300',
  };
  return <span className={`px-2 py-1 rounded text-[11px] ${map[color] || map.gray}`}>{children}</span>;
}