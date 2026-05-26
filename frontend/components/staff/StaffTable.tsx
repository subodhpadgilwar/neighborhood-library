"use client";

import {
  Key,
  Lock,
  Pencil,
  RefreshCw,
  UserX,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/shared/DataTable";
import { formatDate } from "@/lib/dateUtils";
import type { Staff } from "@/types";

interface StaffTableProps {
  staff: Staff[];
  currentStaff: Staff | null;
  onEdit: (staff: Staff) => void;
  onChangePassword: (staff: Staff) => void;
  onDeactivate: (staff: Staff) => void;
  onRestore: (staff: Staff) => void;
}

export function StaffTable({
  staff,
  currentStaff,
  onEdit,
  onChangePassword,
  onDeactivate,
  onRestore,
}: StaffTableProps) {
  const columns: DataTableColumn<Staff>[] = [
    {
      key: "name",
      header: "Full Name",
      className: "font-medium",
      cell: (member) => {
        const isCurrentUser = currentStaff?.id === member.id;
        return (
          <span className="inline-flex items-center gap-2">
            {member.full_name}
            {member.is_default_admin ? (
              <span title="Default admin cannot be deactivated">
                <Lock
                  className="size-3.5 text-muted-foreground"
                  aria-hidden
                />
              </span>
            ) : null}
            {isCurrentUser ? (
              <Badge variant="outline" className="text-xs">
                (You)
              </Badge>
            ) : null}
          </span>
        );
      },
    },
    {
      key: "email",
      header: "Email",
      cell: (member) => member.email,
    },
    {
      key: "status",
      header: "Status",
      cell: (member) =>
        member.is_active ? (
          <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
            Active
          </Badge>
        ) : (
          <Badge
            variant="destructive"
            className="bg-destructive/15 hover:bg-destructive/15"
          >
            Inactive
          </Badge>
        ),
    },
    {
      key: "role",
      header: "Role",
      cell: (member) =>
        member.is_default_admin ? (
          <Badge variant="secondary">Default Admin</Badge>
        ) : (
          <Badge variant="outline">Staff</Badge>
        ),
    },
    {
      key: "joined",
      header: "Joined",
      className: "text-muted-foreground",
      cell: (member) => formatDate(member.created_at),
    },
    {
      key: "actions",
      header: "Actions",
      headerClassName: "text-right",
      className: "text-right",
      cell: (member) => {
        const isCurrentUser = currentStaff?.id === member.id;
        const isDefaultAdmin = member.is_default_admin;

        return member.is_active ? (
          <div className="flex justify-end gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => onEdit(member)}
              aria-label={`Edit ${member.full_name}`}
            >
              <Pencil className="size-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => onChangePassword(member)}
              aria-label={`Change password for ${member.full_name}`}
            >
              <Key className="size-4" />
            </Button>
            {!isDefaultAdmin && !isCurrentUser ? (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="text-destructive hover:text-destructive"
                onClick={() => onDeactivate(member)}
                aria-label={`Deactivate ${member.full_name}`}
              >
                <UserX className="size-4" />
              </Button>
            ) : null}
          </div>
        ) : (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="text-emerald-600 hover:text-emerald-600"
            onClick={() => onRestore(member)}
            aria-label={`Restore ${member.full_name}`}
          >
            <RefreshCw className="size-4" />
          </Button>
        );
      },
    },
  ];

  return (
    <DataTable
      data={staff}
      columns={columns}
      getRowKey={(member) => member.id}
    />
  );
}
