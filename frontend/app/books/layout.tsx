import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Books",
};

export default function BooksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
