import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { NavItem } from "@/config/navigation";

export function ComingSoonPage({ item }: { item: NavItem }) {
  return (
    <>
      <PageHeader title={item.label} description={item.description} />
      <EmptyState
        icon={item.icon}
        title="Not built yet"
        description="This section is part of the roadmap and will appear here as the project progresses."
        action={<Badge variant="muted">Coming soon</Badge>}
      />
    </>
  );
}