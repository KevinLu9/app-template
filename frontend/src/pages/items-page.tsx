import { Plus, Trash2 } from "lucide-react";
import { useState, type FormEvent } from "react";

import { PageHeader } from "@/components/page-header";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useCreateItem, useDeleteItem, useItems } from "@/hooks/use-items";

function CreateItemDialog() {
  const [open, setOpen] = useState(false);
  const createItem = useCreateItem();

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    createItem.mutate(
      { name: String(form.get("name")), description: String(form.get("description")) || null },
      { onSuccess: () => setOpen(false) },
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus /> New item
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>New item</DialogTitle>
            <DialogDescription>
              Stored in Lakebase (local Postgres in development).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" name="name" required maxLength={200} autoFocus />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" name="description" maxLength={2000} />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createItem.isPending}>
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function ItemsPage() {
  const items = useItems();
  const deleteItem = useDeleteItem();
  const { data: user } = useCurrentUser();

  return (
    <>
      <PageHeader
        title="Items"
        description="Reference CRUD example: React → Flask → SQLAlchemy → Lakebase."
        actions={<CreateItemDialog />}
      />
      {items.isPending ? (
        <LoadingState />
      ) : items.isError ? (
        <ErrorState error={items.error} />
      ) : items.data.length === 0 ? (
        <EmptyState title="No items yet">Create one to see the round trip.</EmptyState>
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Created by</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-12" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.data.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.name}</TableCell>
                  <TableCell className="max-w-sm truncate text-muted-foreground">
                    {item.description}
                  </TableCell>
                  <TableCell>{item.created_by}</TableCell>
                  <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    {item.created_by === user?.email && (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Delete ${item.name}`}
                        disabled={deleteItem.isPending}
                        onClick={() => deleteItem.mutate(item.id)}
                      >
                        <Trash2 />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </>
  );
}
