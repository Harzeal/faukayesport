import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white p-6">
      <h1 className="text-5xl font-extrabold text-blue-500 mb-4">FAUKAY ESPORT</h1>
      <p className="text-xl text-gray-400 mb-10 text-center max-w-md">
        Sistem Manajemen Inventaris Barang Esport. Silakan masuk sesuai dengan peran Anda.
      </p>
      
      <div className="flex gap-6">
        <Link href="/login">
          <button className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-xl font-bold transition-all transform hover:scale-105">
            Masuk ke Sistem
          </button>
        </Link>
      </div>
    </div>
  );
}
