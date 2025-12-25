import type { AppProps } from 'next/app';
import Head from 'next/head';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ToastProvider } from '@/components/atoms/Toast';
import { useWebSocketAutoConnect } from '@/hooks/useWebSocketAutoConnect';
import '@/styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  console.log('[App] Rendering page');
  
  // Auto-connect to WebSocket
  useWebSocketAutoConnect();

  return (
    <>
      <Head>
        <title>Distributed Training Dashboard</title>
        <meta name="description" content="Real-time dashboard for distributed machine learning training with blockchain integration" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <ToastProvider>
        <DashboardLayout>
          <Component {...pageProps} />
        </DashboardLayout>
      </ToastProvider>
    </>
  );
}
