import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Lending",
};

export default function LendingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
