import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // The dev overlay sits on top of the bottom nav; keep it out of the way.
  devIndicators: false,
};

export default nextConfig;
