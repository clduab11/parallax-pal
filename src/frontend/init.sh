#!/bin/bash

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Initializing Parallax Pal Frontend...${NC}\n"

# Create necessary directories
echo "Creating directory structure..."
mkdir -p src/{components,contexts,pages,services,styles,utils} public

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
npm install

# Install dev dependencies
echo -e "\n${BLUE}Installing development dependencies...${NC}"
npm install --save-dev \
  @types/react \
  @types/react-dom \
  @types/react-router-dom \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  prettier \
  tailwindcss \
  postcss \
  autoprefixer

# Create Tailwind CSS configuration
echo -e "\n${BLUE}Setting up Tailwind CSS...${NC}"
npx tailwindcss init -p

# Create index.css with Tailwind directives
echo -e "\n${BLUE}Creating base styles...${NC}"
cat > src/styles/index.css << EOL
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50;
  }
}
EOL

# Update index.html
echo -e "\n${BLUE}Creating index.html...${NC}"
cat > public/index.html << EOL
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Parallax Pal - Research and Analytics Platform" />
    <title>Parallax Pal</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOL

# Create index.tsx
echo -e "\n${BLUE}Creating entry point...${NC}"
cat > src/index.tsx << EOL
import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOL

# Update tailwind.config.js
echo -e "\n${BLUE}Configuring Tailwind...${NC}"
cat > tailwind.config.js << EOL
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './public/index.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOL

# Create .env file for development
echo -e "\n${BLUE}Creating environment configuration...${NC}"
cat > .env << EOL
REACT_APP_API_URL=http://localhost:8000
EOL

# Create .gitignore
echo -e "\n${BLUE}Creating .gitignore...${NC}"
cat > .gitignore << EOL
# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# production
/build

# misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*
EOL

# Build the project
echo -e "\n${BLUE}Building the project...${NC}"
npm run build

echo -e "\n${GREEN}Frontend initialization complete!${NC}"
echo -e "You can now start the development server with: ${BLUE}npm start${NC}\n"