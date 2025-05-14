import { withSentryConfig } from '@sentry/nextjs';

/** @type {import('next').NextConfig} */
let nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    domains: [
      // TODO: extract this to env variables
      'workflowai.blob.core.windows.net',
      'workflowaistaging.blob.core.windows.net',
      '127.0.0.1',
      'img.clerk.com',
      'images.clerk.dev',
    ],
  },
  async redirects() {
    return [
      {
        source: '/:tenant/agents/:taskId/:taskSchemaId/playground',
        destination: '/:tenant/agents/:taskId/:taskSchemaId',
        permanent: true,
      },
      {
        source: '/keys',
        destination: '/organization/settings/api-keys',
        permanent: true,
      },
    ];
  },
};

if (process.env.SENTRY_DISABLED != 'true') {
  nextConfig = withSentryConfig(
    nextConfig,
    {
      // For all available options, see:
      // https://github.com/getsentry/sentry-webpack-plugin#options

      // Suppresses source map uploading logs during build
      silent: true,
      org: 'workflowai',
      project: 'workflowai-com',
    },
    {
      // For all available options, see:
      // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

      // Upload a larger set of source maps for prettier stack traces (increases build time)
      widenClientFileUpload: true,

      // Transpiles SDK to be compatible with IE11 (increases bundle size)
      transpileClientSDK: false,

      // Routes browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers. (increases server load)
      // Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
      // side errors will fail.
      tunnelRoute: '/monitoring',

      // Hides source maps from generated client bundles
      hideSourceMaps: true,

      // Automatically tree-shake Sentry logger statements to reduce bundle size
      disableLogger: true,

      // Enables automatic instrumentation of Vercel Cron Monitors.
      // See the following for more information:
      // https://docs.sentry.io/product/crons/
      // https://vercel.com/docs/cron-jobs
      automaticVercelMonitors: false,
      // Automatically annotate React components to show their full name in breadcrumbs and session replay
      reactComponentAnnotation: {
        enabled: true,
      },
    }
  );
}

export default nextConfig;
