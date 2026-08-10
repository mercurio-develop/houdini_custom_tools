/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const api = process.env.PRODUCTION_HUB_API_URL || "http://127.0.0.1:8765";
    return [
      { source: "/api/:path*", destination: `${api}/:path*` },
    ];
  },
};

module.exports = nextConfig;
