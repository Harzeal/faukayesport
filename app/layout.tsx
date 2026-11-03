import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FAUKAY E-SPORT | Live PC & Billing Monitor',
  description:
    'Cek ketersediaan kursi PC VVIP & VIP beserta sisa waktu billing CyberIndo secara real-time di Warnet Faukay E-Sport.',
  icons: {
    icon: '/logo.png',
  },
  verification: {
    google: 'Qy0DRaSCD9UFGrQhSWz5r8-XsKWQVBo7UlvYYLGMDyk',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
