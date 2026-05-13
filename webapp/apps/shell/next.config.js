/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
  experimental: {
    typedRoutes: false,
  },
};

module.exports = nextConfig;
