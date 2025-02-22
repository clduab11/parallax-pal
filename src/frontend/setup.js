const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  red: '\x1b[31m'
};

console.log(`${colors.bright}${colors.blue}Setting up Parallax Pal Frontend...${colors.reset}\n`);

try {
  // Create necessary directories if they don't exist
  const directories = [
    'src/components',
    'src/contexts',
    'src/pages',
    'src/services',
    'src/styles',
    'public'
  ];

  directories.forEach(dir => {
    const fullPath = path.join(__dirname, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
      console.log(`${colors.green}Created directory: ${dir}${colors.reset}`);
    }
  });

  // Install dependencies
  console.log('\nInstalling dependencies...');
  execSync('npm install', { stdio: 'inherit' });

  // Create Tailwind CSS config if it doesn't exist
  const tailwindConfig = 'tailwind.config.js';
  if (!fs.existsSync(path.join(__dirname, tailwindConfig))) {
    console.log('\nCreating Tailwind CSS configuration...');
    execSync('npx tailwindcss init', { stdio: 'inherit' });
  }

  // Create postcss.config.js if it doesn't exist
  const postcssConfig = 'postcss.config.js';
  if (!fs.existsSync(path.join(__dirname, postcssConfig))) {
    fs.writeFileSync(
      path.join(__dirname, postcssConfig),
      `module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}\n`
    );
    console.log(`${colors.green}Created PostCSS configuration${colors.reset}`);
  }

  // Create base CSS file with Tailwind directives
  const cssContent = `@tailwind base;
@tailwind components;
@tailwind utilities;`;

  fs.writeFileSync(path.join(__dirname, 'src/styles/index.css'), cssContent);
  console.log(`${colors.green}Created base CSS file with Tailwind directives${colors.reset}`);

  console.log(`\n${colors.bright}${colors.green}Setup completed successfully!${colors.reset}`);
  console.log(`\nYou can now start the development server with: ${colors.bright}npm start${colors.reset}`);

} catch (error) {
  console.error(`\n${colors.red}Error during setup:${colors.reset}`, error);
  process.exit(1);
}