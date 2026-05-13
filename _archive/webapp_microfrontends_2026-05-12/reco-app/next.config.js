/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  basePath: "/reco",
  assetPrefix: "/reco",
  transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"],
};
module.exports = nextConfig;
