"use client";

import { Eye, Pencil, RefreshCw, UserX } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/shared/DataTable";
import { cn } from "@/lib/utils";
import type { Member } from "@/types";

interface MemberTableProps {
  members: Member[];
  onEdit: (member: Member) => void;
  onViewLoans: (member: Member) => void;
  onDeactivate: (member: Member) => void;
  onRestore: (member: Member) => void;
}

export function MemberTable({
  members,
  onEdit,
  onViewLoans,
  onDeactivate,
  onRestore,
}: MemberTableProps) {
  const columns: DataTableColumn<Member>[] = [
    {
      key: "name",
      header: "Name",
      className: "max-w-[160px] truncate font-medium",
      cell: (member) => (
        <span
          className={cn(
            !member.is_active && "text-muted-foreground line-through",
          )}
        >
          {member.name}
        </span>
      ),
    },
    {
      key: "email",
      header: "Email",
      className: "max-w-[200px] truncate",
      cell: (member) => (
        <span className={cn(!member.is_active && "text-muted-foreground")}>
          {member.email}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      cell: (member) =>
        !member.is_active ? (
          <Badge
            variant="destructive"
            className="bg-destructive/15 hover:bg-destructive/15"
          >
            Inactive
          </Badge>
        ) : null,
    },
    {
      key: "phone",
      header: "Phone",
      className: "text-muted-foreground",
      cell: (member) => member.phone ?? "—",
    },
    {
      key: "address",
      header: "Address",
      className: "max-w-[200px] truncate text-muted-foreground",
      cell: (member) => member.address ?? "—",
    },
    {
      key: "registeredBy",
      header: "Registered By",
      className: "text-muted-foreground",
      cell: (member) => member.created_by ?? "—",
    },
    {
      key: "actions",
      header: "Actions",
      headerClassName: "w-[130px] text-right",
      className: "text-right",
      cell: (member) =>
        member.is_active ? (
          <div className="flex justify-end gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => onViewLoans(member)}
              aria-label={`View loans for ${member.name}`}
            >
              <Eye className="size-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => onEdit(member)}
              aria-label={`Edit ${member.name}`}
            >
              <Pencil className="size-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="text-destructive hover:text-destructive"
              onClick={() => onDeactivate(member)}
              aria-label={`Deactivate ${member.name}`}
            >
              <UserX className="size-4" />
            </Button>
          </div>
        ) : (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="text-emerald-600 hover:text-emerald-600"
            onClick={() => onRestore(member)}
            aria-label={`Restore ${member.name}`}
          >
            <RefreshCw className="size-4" />
          </Button>
        ),
    },
  ];

  return (
    <DataTable
      data={members}
      columns={columns}
      getRowKey={(member) => member.id}
      getRowClassName={(member) => cn(!member.is_active && "opacity-60")}
    />
  );
}
