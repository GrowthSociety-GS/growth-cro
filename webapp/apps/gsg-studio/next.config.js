/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  basePath: "/gsg",
  assetPrefix: "/gsg",
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
};
module.exports = nextConfig;
