import { AlertCircle, Inbox } from "lucide-react";
import type { ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";

/** Standard loading / empty / error states. Use these instead of ad-hoc versions. */

export function LoadingState({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy="true">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-10 text-center">
      <Inbox className="mb-3 size-8 text-muted-foreground" />
      <p className="font-medium">{title}</p>
      {children && <div className="mt-2 text-sm text-muted-foreground">{children}</div>}
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  const requestId = error instanceof ApiError ? error.requestId : undefined;
  return (
    <Alert variant="destructive">
      <AlertCircle />
      <AlertTitle>Request failed</AlertTitle>
      <AlertDescription>
        <p>{message}</p>
        {requestId && <p className="text-xs">Request ID: {requestId}</p>}
      </AlertDescription>
    </Alert>
  );
}
