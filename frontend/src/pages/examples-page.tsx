import { useQuery } from "@tanstack/react-query";
import { Play, ServerCog, User } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { ErrorState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api";

type Identity = "obo" | "sp";

const EXAMPLES = [
  { path: "whoami", label: "Workspace API: current_user.me()" },
  { path: "warehouse", label: "SQL warehouse: SELECT current_user()" },
  { path: "sample-trips?limit=5", label: "SQL warehouse: samples.nyctaxi.trips", oboOnly: true },
];

function ExampleRunner({
  identity,
  path,
  label,
}: {
  identity: Identity;
  path: string;
  label: string;
}) {
  const query = useQuery({
    queryKey: ["examples", identity, path],
    queryFn: () => apiGet<unknown>(`/examples/${identity}/${path}`),
    enabled: false,
    retry: false,
  });

  return (
    <div className="space-y-2 rounded-lg border p-3">
      <div className="flex items-center justify-between gap-2">
        <code className="text-sm">{label}</code>
        <Button
          size="sm"
          variant="outline"
          onClick={() => query.refetch()}
          disabled={query.isFetching}
        >
          <Play /> Run
        </Button>
      </div>
      {query.isError && <ErrorState error={query.error} />}
      {query.data !== undefined && (
        <pre className="max-h-64 overflow-auto rounded bg-muted p-2 text-xs">
          {JSON.stringify(query.data, null, 2)}
        </pre>
      )}
    </div>
  );
}

const COLUMNS = [
  {
    identity: "obo" as const,
    icon: User,
    title: "On behalf of the user (OBO)",
    description:
      "Uses the X-Forwarded-Access-Token header. Unity Catalog permissions of the signed-in user apply.",
  },
  {
    identity: "sp" as const,
    icon: ServerCog,
    title: "As the app service principal (SP)",
    description:
      "Uses the app's own credentials. Every user gets the same access, so the app must enforce authorization.",
  },
];

export function ExamplesPage() {
  return (
    <>
      <PageHeader
        title="OBO vs service principal"
        description="Run the same calls with both identities and compare who Databricks thinks you are. Locally, both use your CLI profile."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {COLUMNS.map(({ identity, icon: Icon, title, description }) => (
          <Card key={identity}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Icon className="size-5" /> {title}
                <Badge variant="outline">{identity.toUpperCase()}</Badge>
              </CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {EXAMPLES.filter((e) => identity === "obo" || !e.oboOnly).map((example) => (
                <ExampleRunner key={example.path} identity={identity} {...example} />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
