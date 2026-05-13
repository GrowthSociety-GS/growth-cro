/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  basePath: "/audit",
  assetPrefix: "/audit",
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
};
module.exports = nextConfig;
