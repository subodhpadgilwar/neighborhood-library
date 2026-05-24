"use client";

import { Search, UserPlus } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { AppLayout } from "@/components/layout/AppLayout";
import { MemberFormModal } from "@/components/members/MemberFormModal";
import { MemberLoansModal } from "@/components/members/MemberLoansModal";
import { MemberTable } from "@/components/members/MemberTable";
import { DeactivateConfirmDialog } from "@/components/shared/DeactivateConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { memberService } from "@/services";
import type { Member } from "@/types";

const PAGE_SIZE = 10;

function sortByName(members: Member[]): Member[] {
  return [...members].sort((a, b) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
  );
}

function MembersPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [loansModalOpen, setLoansModalOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<Member | null>(null);
  const [loansMember, setLoansMember] = useState<Member | null>(null);
  const [showInactive, setShowInactive] = useState(false);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);

  const loadMembers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await memberService.getAll(0, 1000, showInactive);
      setMembers(data);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load members.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [showInactive]);

  useEffect(() => {
    void loadMembers();
  }, [loadMembers]);

  useEffect(() => {
    if (searchParams.get("action") === "register") {
      setEditingMember(null);
      setFormModalOpen(true);
      router.replace("/members", { scroll: false });
    }
  }, [searchParams, router]);

  const filteredMembers = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return members;
    }
    return members.filter(
      (member) =>
        member.name.toLowerCase().includes(query) ||
        member.email.toLowerCase().includes(query),
    );
  }, [members, search]);

  const sortedMembers = useMemo(
    () => sortByName(filteredMembers),
    [filteredMembers],
  );

  const totalPages = Math.max(1, Math.ceil(sortedMembers.length / PAGE_SIZE));

  const paginatedMembers = useMemo(() => {
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * PAGE_SIZE;
    return sortedMembers.slice(start, start + PAGE_SIZE);
  }, [sortedMembers, page, totalPages]);

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  function openCreateModal() {
    setEditingMember(null);
    setFormModalOpen(true);
  }

  function openEditModal(member: Member) {
    setEditingMember(member);
    setFormModalOpen(true);
  }

  function openLoansModal(member: Member) {
    setLoansMember(member);
    setLoansModalOpen(true);
  }

  function handleFormModalOpenChange(open: boolean) {
    setFormModalOpen(open);
    if (!open) {
      setEditingMember(null);
    }
  }

  function handleLoansModalOpenChange(open: boolean) {
    setLoansModalOpen(open);
    if (!open) {
      setLoansMember(null);
    }
  }

  function handleDeactivate(member: Member) {
    setSelectedMember(member);
    setIsDeactivateModalOpen(true);
  }

  async function handleRestore(member: Member) {
    try {
      await memberService.restore(member.id);
      toast.success("Member restored successfully");
      void loadMembers();
    } catch (err) {
      const apiError = err as { message?: string };
      toast.error(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to restore member.",
      );
    }
  }

  function handleDeactivateSuccess() {
    setIsDeactivateModalOpen(false);
    setSelectedMember(null);
    void loadMembers();
  }

  const isEmpty = !isLoading && !error && sortedMembers.length === 0;

  return (
    <AppLayout title="Members">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center">
            <div className="flex items-center gap-3">
              <Switch
                id="show-inactive-members"
                checked={showInactive}
                onCheckedChange={setShowInactive}
                disabled={isLoading}
              />
              <Label htmlFor="show-inactive-members" className="cursor-pointer">
                Show inactive
              </Label>
            </div>
            <div className="relative max-w-md flex-1">
              <Search
                className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden
              />
              <Input
                type="search"
                placeholder="Search by name or email…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
                disabled={isLoading}
              />
            </div>
          </div>
          <Button onClick={openCreateModal} className="shrink-0 gap-2">
            <UserPlus className="size-4" aria-hidden />
            Register Member
          </Button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}

        {isLoading ? (
          <LoadingSkeleton rows={6} columns={7} />
        ) : isEmpty ? (
          <EmptyState
            message="No members found"
            actionLabel="Register Member"
            onAction={openCreateModal}
          />
        ) : (
          <>
            <MemberTable
              members={paginatedMembers}
              onEdit={openEditModal}
              onViewLoans={openLoansModal}
              onDeactivate={handleDeactivate}
              onRestore={handleRestore}
            />

            {totalPages > 1 ? (
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm text-muted-foreground">
                  Showing {(page - 1) * PAGE_SIZE + 1}–
                  {Math.min(page * PAGE_SIZE, sortedMembers.length)} of{" "}
                  {sortedMembers.length}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    Previous
                  </Button>
                  <span className="text-sm tabular-nums">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        )}
      </div>

      <MemberFormModal
        open={formModalOpen}
        onOpenChange={handleFormModalOpenChange}
        member={editingMember}
        onSuccess={() => void loadMembers()}
      />

      <MemberLoansModal
        open={loansModalOpen}
        onOpenChange={handleLoansModalOpenChange}
        member={loansMember}
      />

      <DeactivateConfirmDialog
        isOpen={isDeactivateModalOpen}
        onClose={() => setIsDeactivateModalOpen(false)}
        onSuccess={handleDeactivateSuccess}
        entityType="member"
        entityName={selectedMember?.name ?? ""}
        id={selectedMember?.id ?? ""}
        onConfirm={memberService.deactivate}
      />
    </AppLayout>
  );
}

function MembersPageFallback() {
  return (
    <AppLayout title="Members">
      <LoadingSkeleton rows={6} columns={7} />
    </AppLayout>
  );
}

export default function MembersPage() {
  return (
    <Suspense fallback={<MembersPageFallback />}>
      <MembersPageContent />
    </Suspense>
  );
}
