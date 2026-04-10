/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // Remplacez 'nom-du-repo' par le nom de votre projet GitHub
  basePath: '/Hackathon-Open-data-University', 
  // Permet de gérer les images correctement sans serveur d'optimisation
  images: {
    unoptimized: true,
  },
};

export default nextConfig;