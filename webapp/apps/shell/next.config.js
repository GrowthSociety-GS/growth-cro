/** @type {import('next').NextConfig} */
const path = require("path");

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
  experimental: {
    typedRoutes: false,
  },
  async rewrites() {
    // Microfrontends routing: in dev, fall back to localhost. In prod, Vercel
    // microfrontends config (microfrontends.json) takes over via @vercel/microfrontends.
    const dev = process.env.NODE_ENV !== "production";
    if (!dev) return [];
    return [
      {
        source: "/audit/:path*",
        destination: "http://localhost:3001/audit/:path*",
      },
      {
        source: "/reco/:path*",
        destination: "http://localhost:3002/reco/:path*",
      },
      {
        source: "/gsg/:path*",
        destination: "http://localhost:3003/gsg/:path*",
      },
      {
        source: "/reality/:path*",
        destination: "http://localhost:3004/reality/:path*",
      },
      {
        source: "/learning/:path*",
        destination: "http://localhost:3005/learning/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
