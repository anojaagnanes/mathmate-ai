import type { NextConfig } from 'next';
const config: NextConfig = {
  output: 'standalone',
  // Local CPU vision has a bounded 180s backend deadline; do not cut it off at 30s.
  experimental: {proxyTimeout: 210000},
  async rewrites() { return [{source: '/api/v1/:path*', destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/v1/:path*`}]; },
  async headers() { return [{source: '/:path*', headers: [{key: 'X-Content-Type-Options', value: 'nosniff'}, {key: 'X-Frame-Options', value: 'DENY'}, {key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin'}]}]; }
};
export default config;
