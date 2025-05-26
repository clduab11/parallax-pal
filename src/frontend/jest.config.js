module.exports = {
  preset: 'react-scripts',
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    // Handle CSS imports
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // Handle image imports
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
    // Handle ES modules
    '^react-force-graph-2d$': '<rootDir>/__mocks__/react-force-graph-2d.js',
    '^react-kapsule$': '<rootDir>/__mocks__/react-kapsule.js'
  },
  transformIgnorePatterns: [
    'node_modules/(?!(react-force-graph-2d|react-kapsule|force-graph)/)'
  ],
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{spec,test}.{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
    '!src/setupTests.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};