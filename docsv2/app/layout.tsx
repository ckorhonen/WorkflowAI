import './global.css';
import { RootProvider } from 'fumadocs-ui/provider';
import { Banner } from 'fumadocs-ui/components/banner';
import { Inter } from 'next/font/google';
import type { ReactNode } from 'react';

const inter = Inter({
  subsets: ['latin'],
});

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={inter.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <Banner>
          Launching WorkflowAI (
          <a
            href="https://fumadocs.dev/docs/ui/components/banner"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            banner
          </a>
          )
        </Banner>
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
