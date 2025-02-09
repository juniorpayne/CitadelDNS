import { TextInput, NumberInput, Button, Select, Stack, Paper, rem } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useMutation } from '@tanstack/react-query';
import { dnsApi, DNSRecord } from '../api/client';

interface DNSRecordFormValues extends DNSRecord {
  zoneName: string;
  type: 'A' | 'TXT';
}

export function DNSRecordForm() {
  const form = useForm<DNSRecordFormValues>({
    initialValues: {
      zoneName: '',
      name: '',
      content: '',
      ttl: 3600,
      type: 'A',
    },
    validate: {
      zoneName: (value) => (!value ? 'Zone name is required' : null),
      name: (value) => (!value ? 'Record name is required' : null),
      content: (value) => (!value ? 'Content is required' : null),
      ttl: (value) => (value < 1 || value > 86400 ? 'TTL must be between 1 and 86400' : null),
    },
  });

  const createRecord = useMutation({
    mutationFn: async (values: DNSRecordFormValues) => {
      const { zoneName, type, ...record } = values;
      if (type === 'A') {
        return dnsApi.createARecord(zoneName, record);
      } else {
        return dnsApi.createTXTRecord(zoneName, record);
      }
    },
    onSuccess: () => {
      notifications.show({
        title: 'Success',
        message: 'DNS record created successfully',
        color: 'green',
      });
      form.reset();
    },
    onError: (error: any) => {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to create DNS record',
        color: 'red',
      });
    },
  });

  const handleSubmit = form.onSubmit((values) => {
    createRecord.mutate(values);
  });

  return (
    <Paper shadow="xs" p={rem(20)} radius="md" withBorder>
      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <TextInput
            label="Zone Name"
            placeholder="example.com"
            required
            {...form.getInputProps('zoneName')}
          />

          <TextInput
            label="Record Name"
            placeholder="www"
            description="Subdomain or @ for root domain"
            required
            {...form.getInputProps('name')}
          />

          <Select
            label="Record Type"
            data={[
              { value: 'A', label: 'A Record (IPv4)' },
              { value: 'TXT', label: 'TXT Record' },
            ]}
            required
            {...form.getInputProps('type')}
          />

          <TextInput
            label="Content"
            placeholder={form.values.type === 'A' ? '192.168.1.1' : 'v=spf1 include:_spf.example.com ~all'}
            description={form.values.type === 'A' ? 'IPv4 address' : 'Text content'}
            required
            {...form.getInputProps('content')}
          />

          <NumberInput
            label="TTL (Time To Live)"
            description="Time in seconds (1-86400)"
            min={1}
            max={86400}
            required
            {...form.getInputProps('ttl')}
          />

          <Button
            type="submit"
            loading={createRecord.isPending}
            mt="md"
          >
            Create DNS Record
          </Button>
        </Stack>
      </form>
    </Paper>
  );
}