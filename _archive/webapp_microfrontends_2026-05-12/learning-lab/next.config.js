/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  basePath: "/learning",
  assetPrefix: "/learning",
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
};
module.exports = nextConfig;
