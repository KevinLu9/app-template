import { Database, FlaskConical, ShieldCheck } from "lucide-react";
import { Link } from "react-router";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCurrentUser } from "@/hooks/use-current-user";

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Databricks authentication",
    body: "Users are signed in by Databricks. The backend reads identity from proxy headers only.",
  },
  {
    icon: Database,
    title: "Lakebase + Lakehouse",
    body: "SQLAlchemy for Lakebase (Postgres) and for SQL warehouses via Unity Catalog.",
  },
  {
    icon: FlaskConical,
    title: "OBO and service principal",
    body: "Examples of calling Databricks as the signed-in user or as the app itself.",
  },
];

export function HomePage() {
  const { data: user } = useCurrentUser();

  return (
    <>
      <PageHeader
        title={user ? `Welcome, ${user.display_name}` : "Welcome"}
        description="This is the company app template. Replace this page with your app."
        actions={
          <Button asChild>
            <Link to="/items">Try the Items example</Link>
          </Button>
        }
      />
      <div className="grid gap-4 md:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <Card key={title}>
            <CardHeader>
              <Icon className="mb-2 size-5 text-muted-foreground" />
              <CardTitle>{title}</CardTitle>
              <CardDescription>{body}</CardDescription>
            </CardHeader>
            <CardContent />
          </Card>
        ))}
      </div>
    </>
  );
}
