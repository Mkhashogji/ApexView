const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@ui/primitives', '@models/types'],
  output: 'standalone',  // Enable standalone mode for Docker
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  async redirects() {
    return [
      {
        source: '/track/:round',
        destination: '/track?round=:round',
        permanent: true,
      },
    ]
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks?.cacheGroups,
          // Isolate Plotly into its own chunk — loaded only by chart components
          plotly: {
            test: /[\\/]node_modules[\\/](plotly\.js|plotly\.js-cartesian-dist-min|react-plotly\.js)[\\/]/,
            name: 'plotly',
            chunks: 'all',
            priority: 30,
          },
        },
      }
    }
    return config
  },
}

module.exports = withBundleAnalyzer(nextConfig)

