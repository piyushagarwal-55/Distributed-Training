/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  // Optimize for production
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error', 'warn'] } : false,
  },
  // Image optimization
  images: {
    domains: [],
  },
  // Environment variables
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
    WS_URL: process.env.WS_URL || 'ws://localhost:8000/ws',
  },
}

module.exports = nextConfig
