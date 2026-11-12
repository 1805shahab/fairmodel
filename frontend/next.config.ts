import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep Windows/local launch commands unchanged; package only the cloud image.
  output: process.env.FAIRMODEL_STANDALONE === "true" ? "standalone" : undefined,
  poweredByHeader: false,
  experimental: { proxyClientMaxBodySize: "25mb" },
};
export default nextConfig;
