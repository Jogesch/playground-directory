import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import image from '@astrojs/image';

export default defineConfig({
  integrations: [
    tailwind(),
    image({
      serviceEntryPoint: '@astrojs/image/sharp'
    })
  ],
  site: 'https://london-playgrounds.netlify.app', // Update this with your actual domain
  output: 'static'
}); 