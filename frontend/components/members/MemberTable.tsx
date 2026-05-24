"use client";

import { Eye, Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Member } from "@/types";

interface MemberTableProps {
  members: Member[];
  onEdit: (member: Member) => void;
  onViewLoans: (member: Member) => void;
}

export function MemberTable({
  members,
  onEdit,
  onViewLoans,
}: MemberTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead>Address</TableHead>
          <TableHead>Registered By</TableHead>
          <TableHead className="w-[100px] text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {members.map((member) => (
          <TableRow key={member.id}>
            <TableCell className="max-w-[160px] truncate font-medium">
              {member.name}
            </TableCell>
            <TableCell className="max-w-[200px] truncate">
              {member.email}
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
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
