import { supabase } from '@/lib/supabase';

export async function POST(request: Request) {
  const { username, password } = await request.json();

  // Gunakan nama tabel 'pengguna' dan nama kolom sesuai gambar kamu
  const { data: user, error } = await supabase
    .from('User') // Sesuai nama di gambar image_49b403.png
    .select('*')
    .eq('Nama belakang', username) // Sesuai kolom di image_49b403.png
    .eq('Kata sandi', password) 
    .single();

  if (user) {
    return Response.json({ success: true, user });
  } else {
    return Response.json({ success: false, message: "Akun tidak ditemukan" }, { status: 401 });
  }
}
