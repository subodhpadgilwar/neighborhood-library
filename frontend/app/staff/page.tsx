"use client";

import { Plus } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { AppLayout } from "@/components/layout/AppLayout";
import { ChangePasswordModal } from "@/components/staff/ChangePasswordModal";
import { DeactivateConfirmDialog } from "@/components/staff/DeactivateConfirmDialog";
import { StaffFormModal } from "@/components/staff/StaffFormModal";
import { StaffTable } from "@/components/staff/StaffTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Pagination } from "@/components/shared/Pagination";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { usePaginatedQuery } from "@/hooks/usePaginatedQuery";
import { useAuth } from "@/lib/authContext";
import { staffService } from "@/services";
import type { Staff } from "@/types";

type ApiClientError = { status: string; message: string };

const DEFAULT_PAGE_SIZE = 25;

export default function StaffPage() {
  const { staff: currentStaff } = useAuth();

  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInactive, setShowInactive] = useState(false);
  const [totalStaff, setTotalStaff] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [selectedStaff, setSelectedStaff] = useState<Staff | null>(null);

  const { page, limit, setPage, setLimit } = usePaginatedQuery({
    defaultLimit: DEFAULT_PAGE_SIZE,
  });

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] =
    useState(false);
  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);
  const [changePasswordMode, setChangePasswordMode] = useState<"own" | "admin">(
    "admin",
  );

  const fetchStaff = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await staffService.getPage({
        page,
        limit,
        includeInactive: showInactive,
        sortBy: "full_name",
        sortOrder: "asc",
      });
      setStaffList(data.items);
      setTotalStaff(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      const apiError = err as ApiClientError;
      setError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load staff.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [limit, page, showInactive]);

  useDeferredEffect(() => {
    void fetchStaff();
  }, [fetchStaff]);

  function handleSuccess() {
    setIsCreateModalOpen(false);
    setIsEditModalOpen(false);
    setIsChangePasswordModalOpen(false);
    setIsDeactivateModalOpen(false);
    setSelectedStaff(null);
    void fetchStaff();
  }

  function handlePageChange(nextPage: number) {
    setPage(nextPage);
  }

  function handleLimitChange(nextLimit: number) {
    setLimit(nextLimit);
  }

  function handleEdit(staff: Staff) {
    setSelectedStaff(staff);
    setIsEditModalOpen(true);
  }

  function handleChangePassword(staff: Staff) {
    setSelectedStaff(staff);
    setChangePasswordMode("admin");
    setIsChangePasswordModalOpen(true);
  }

  function handleDeactivate(staff: Staff) {
    setSelectedStaff(staff);
    setIsDeactivateModalOpen(true);
  }

  async function handleRestore(staff: Staff) {
    try {
      await staffService.restore(staff.id);
      toast.success(`${staff.full_name} has been restored`);
      void fetchStaff();
    } catch (err) {
      const apiError = err as ApiClientError;
      toast.error(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to restore staff member.",
      );
    }
  }

  const currentStaffRecord: Staff | null = currentStaff
    ? {
        id: currentStaff.id,
        full_name: currentStaff.full_name,
        email: currentStaff.email,
        role: currentStaff.role,
        is_active: currentStaff.is_active ?? true,
        is_default_admin: currentStaff.is_default_admin,
        created_at: currentStaff.created_at,
        updated_at: currentStaff.updated_at ?? currentStaff.created_at,
      }
    : null;

  const isEmpty = !isLoading && !error && staffList.length === 0;

  return (
    <AppLayout title="Staff Management">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Switch
              id="show-inactive"
              checked={showInactive}
              onCheckedChange={setShowInactive}
              disabled={isLoading}
            />
            <Label htmlFor="show-inactive" className="cursor-pointer">
              Show inactive
            </Label>
          </div>
          <Button
            onClick={() => setIsCreateModalOpen(true)}
            className="shrink-0 gap-2"
          >
            <Plus className="size-4" aria-hidden />
            Add Staff
          </Button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}

        {isLoading ? (
          <LoadingSkeleton rows={5} columns={6} />
        ) : isEmpty ? (
          <EmptyState
            message="No staff members found"
            actionLabel="Add Staff"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="space-y-4">
            <StaffTable
              staff={staffList}
              currentStaff={currentStaffRecord}
              onEdit={handleEdit}
              onChangePassword={handleChangePassword}
              onDeactivate={handleDeactivate}
              onRestore={handleRestore}
            />

            {totalStaff > 0 ? (
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                totalItems={totalStaff}
                itemsPerPage={limit}
                onPageChange={handlePageChange}
                onLimitChange={handleLimitChange}
              />
            ) : null}
          </div>
        )}
      </div>

      <StaffFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleSuccess}
        mode="create"
      />

      <StaffFormModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedStaff(null);
        }}
        onSuccess={handleSuccess}
        mode="edit"
        initialData={selectedStaff}
      />

      <ChangePasswordModal
        isOpen={isChangePasswordModalOpen}
        onClose={() => {
          setIsChangePasswordModalOpen(false);
          setSelectedStaff(null);
        }}
        mode={changePasswordMode}
        targetStaff={changePasswordMode === "admin" ? selectedStaff : null}
      />

      <DeactivateConfirmDialog
        isOpen={isDeactivateModalOpen}
        onClose={() => {
          setIsDeactivateModalOpen(false);
          setSelectedStaff(null);
        }}
        onSuccess={handleSuccess}
        staff={selectedStaff}
      />
    </AppLayout>
  );
}
