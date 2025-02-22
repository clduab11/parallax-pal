const { execSync } = require('child_process');
const { writeFileSync } = require('fs');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  red: '\x1b[31m'
};

console.log(`${colors.bright}${colors.blue}Setting up development environment...${colors.reset}\n`);

try {
  // Install TypeScript and type definitions
  console.log(`${colors.blue}Installing TypeScript and type definitions...${colors.reset}`);
  execSync('npm install --save-dev typescript @types/node @types/react @types/react-dom @types/react-router-dom @types/jest @types/axios', { stdio: 'inherit' });

  // Create TypeScript config if it doesn't exist
  console.log(`\n${colors.blue}Creating TypeScript configuration...${colors.reset}`);
  const tsConfig = {
    compilerOptions: {
      target: "es5",
      lib: ["dom", "dom.iterable", "esnext"],
      allowJs: true,
      skipLibCheck: true,
      esModuleInterop: true,
      allowSyntheticDefaultImports: true,
      strict: true,
      forceConsistentCasingInFileNames: true,
      noFallthroughCasesInSwitch: true,
      module: "esnext",
      moduleResolution: "node",
      resolveJsonModule: true,
      isolatedModules: true,
      noEmit: true,
      jsx: "react-jsx",
      baseUrl: "src"
    },
    include: ["src"],
    exclude: ["node_modules"]
  };

  writeFileSync('tsconfig.json', JSON.stringify(tsConfig, null, 2));

  // Install ESLint and Prettier
  console.log(`\n${colors.blue}Installing ESLint and Prettier...${colors.reset}`);
  execSync('npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-react eslint-plugin-react-hooks prettier eslint-config-prettier eslint-plugin-prettier', { stdio: 'inherit' });

  // Create ESLint config
  const eslintConfig = {
    parser: "@typescript-eslint/parser",
    extends: [
      "eslint:recommended",
      "plugin:react/recommended",
      "plugin:@typescript-eslint/recommended",
      "prettier",
      "plugin:prettier/recommended"
    ],
    plugins: ["react", "@typescript-eslint", "prettier"],
    env: {
      browser: true,
      es2021: true,
      jest: true
    },
    rules: {
      "prettier/prettier": "error",
      "react/react-in-jsx-scope": "off"
    },
    settings: {
      react: {
        version: "detect"
      }
    }
  };

  writeFileSync('.eslintrc.json', JSON.stringify(eslintConfig, null, 2));

  // Create Prettier config
  const prettierConfig = {
    semi: true,
    trailingComma: "es5",
    singleQuote: true,
    printWidth: 100,
    tabWidth: 2,
    endOfLine: "auto"
  };

  writeFileSync('.prettierrc', JSON.stringify(prettierConfig, null, 2));

  // Install testing libraries
  console.log(`\n${colors.blue}Installing testing libraries...${colors.reset}`);
  execSync('npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest', { stdio: 'inherit' });

  console.log(`\n${colors.green}Development environment setup complete!${colors.reset}`);
  console.log(`\nYou can now start development with: ${colors.bright}npm start${colors.reset}`);

} catch (error) {
  console.error(`\n${colors.red}Error during setup:${colors.reset}`, error);
  process.exit(1);
}