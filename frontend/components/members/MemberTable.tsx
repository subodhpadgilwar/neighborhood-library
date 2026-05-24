"use client";

import { Eye, Pencil, RefreshCw, UserX } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead>Address</TableHead>
          <TableHead>Registered By</TableHead>
          <TableHead className="w-[130px] text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {members.map((member) => {
          const isActive = member.is_active;

          return (
            <TableRow
              key={member.id}
              className={cn(!isActive && "opacity-60")}
            >
              <TableCell
                className={cn(
                  "max-w-[160px] truncate font-medium",
                  !isActive && "text-muted-foreground line-through",
                )}
              >
                {member.name}
              </TableCell>
              <TableCell
                className={cn(
                  "max-w-[200px] truncate",
                  !isActive && "text-muted-foreground",
                )}
              >
                {member.email}
              </TableCell>
              <TableCell>
                {!isActive ? (
                  <Badge
                    variant="destructive"
                    className="bg-destructive/15 hover:bg-destructive/15"
                  >
                    Inactive
                  </Badge>
                ) : null}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {member.phone ?? "—"}
              </TableCell>
              <TableCell className="max-w-[200px] truncate text-muted-foreground">
                {member.address ?? "—"}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {member.created_by ?? "—"}
              </TableCell>
              <TableCell className="text-right">
                {isActive ? (
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
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
