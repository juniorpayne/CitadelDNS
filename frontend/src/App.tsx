import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { DNSRecordForm } from './components/DNSRecordForm';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        <Notifications />
        <Layout>
          <DNSRecordForm />
        </Layout>
      </MantineProvider>
    </QueryClientProvider>
  );
}

export default App;
