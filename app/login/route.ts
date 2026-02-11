import { supabase } from '@/lib/supabase';

export async function POST(request: Request) {
  const { username, password } = await request.json();

  // Mencari user di tabel 'users' pada Supabase
  const { data: user, error } = await supabase
    .from('users')
    .select('*')
    .eq('username', username)
    .eq('password', password) // Catatan: Sebaiknya gunakan hashing password nantinya
    .single();

  if (user) {
    return Response.json({ success: true, message: "Login Berhasil" });
  } else {
    return Response.json({ success: false, message: "Data tidak ditemukan" }, { status: 401 });
  }
}
