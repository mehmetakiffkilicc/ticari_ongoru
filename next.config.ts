import type { NextConfig } from 'next';
const config: NextConfig = { poweredByHeader: false, devIndicators: false, turbopack: { root: process.cwd() }, outputFileTracingIncludes: { '/api/data': ['./analysis/*.py'] } };
export default config;
