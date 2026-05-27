export const apiPaths = {
  auth: {
    login: "/auth/login",
    me: "/auth/me",
  },
  books: {
    list: "/books",
    byId: (id: string) => `/books/${id}`,
    byISBN: (isbn: string) => `/books/isbn/${encodeURIComponent(isbn)}`,
    restore: (id: string) => `/books/${id}/restore`,
  },
  members: {
    list: "/members",
    byId: (id: string) => `/members/${id}`,
    loans: (id: string) => `/members/${id}/loans`,
    restore: (id: string) => `/members/${id}/restore`,
  },
  staff: {
    list: "/staff/",
    byId: (id: string) => `/staff/${id}`,
    restore: (id: string) => `/staff/${id}/restore`,
    changeOwnPassword: "/staff/me/change-password",
    adminChangePassword: (id: string) => `/staff/${id}/change-password`,
  },
  lending: {
    list: "/lending",
    overdue: "/lending/overdue",
    borrow: "/lending/borrow",
    history: "/lending/history",
    returnBook: (id: string) => `/lending/${id}/return`,
    dueDate: (id: string) => `/lending/${id}/due-date`,
  },
  analytics: {
    summary: "/analytics/summary",
    genreDistribution: "/analytics/genre-distribution",
    monthlyLending: "/analytics/monthly-lending",
    topBooks: "/analytics/top-books",
  },
} as const;
