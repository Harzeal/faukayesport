import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: 'Faukay Esport',
  description: 'Sistem Manajemen Inventaris Esport',
  // Tambahkan baris di bawah ini
  verification: {
    google: '<meta name="google-site-verification" content="Qy0DRaSCD9UFGrQhSWz5r8-XsKWQVBo7UlvYYLGMDyk" />',
  },
}
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
