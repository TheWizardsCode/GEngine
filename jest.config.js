/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['**/tests/{unit,validate-story}/**/*.test.[jt]s'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
};
