/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  basePath: "/reality",
  assetPrefix: "/reality",
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
};
module.exports = nextConfig;
