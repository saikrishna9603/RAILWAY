/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Only use static export in production builds, not in dev server
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  basePath: '/RAILWAY',
  assetPrefix: '/RAILWAY/',
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  webpack: (config) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      path: false,
      crypto: false,
    };
    return config;
  },
};

export default nextConfig;
