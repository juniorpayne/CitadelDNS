import { AppShell, Header, Title, Container } from '@mantine/core';
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <AppShell
      padding="md"
      header={
        <Header height={60} p="xs">
          <Title order={1}>CitadelDNS Manager</Title>
        </Header>
      }
    >
      <Container size="lg">
        {children}
      </Container>
    </AppShell>
  );
}