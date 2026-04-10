import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  // Si ton site est sur https://ton-nom.github.io/mon-repo/
  // décommente la ligne suivante et remplace 'mon-repo' :
  basePath: '/Hackathon-Open-data-University',
  images: {
    unoptimized: true,
  },
};

export default nextConfig;