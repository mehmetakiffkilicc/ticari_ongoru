import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'node:child_process';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const MAX_BYTES = 20 * 1024 * 1024;

function engine(payload: Record<string, unknown>): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const child = spawn(/* turbopackIgnore: true */ process.env.PYTHON_PATH || 'python', ['-m', 'analysis.web_engine'], {
      cwd: process.cwd(), windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = ''; let bytes = 0;
    const timer = setTimeout(() => { child.kill(); reject(new Error('Kontrol süresi aşıldı. Dosyayı daha küçük parçalara ayırın.')); }, 120000);
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', (chunk: string) => { bytes += Buffer.byteLength(chunk); if (bytes > 40 * 1024 * 1024) { child.kill(); reject(new Error('Kontrol çıktısı çok büyük. Dosyayı bölün.')); } else stdout += chunk; });
    child.stderr.on('data', () => {});
    child.on('error', () => { clearTimeout(timer); reject(new Error('Python başlatılamadı. PYTHON_PATH ayarını kontrol edin.')); });
    child.on('close', code => {
      clearTimeout(timer);
      if (code !== 0) return reject(new Error('Veri kontrolü tamamlanamadı.'));
      try {
        const result = JSON.parse(stdout) as { ok?: boolean; error?: string };
        if (result.ok === false) return reject(new Error(result.error || 'İşlem tamamlanamadı.'));
        resolve(result);
      } catch (error) {
        reject(error instanceof SyntaxError ? new Error('Analiz yanıtı okunamadı.') : error);
      }
    });
    child.stdin.on('error', () => {});
    child.stdin.end(JSON.stringify(payload));
  });
}

export async function GET() {
  try { return NextResponse.json(await engine({ action: 'list' }), { headers: { 'Cache-Control': 'no-store' } }); }
  catch (e) { return NextResponse.json({ ok: false, error: (e as Error).message }, { status: 500 }); }
}

export async function POST(request: NextRequest) {
  // Local demo: reject cross-origin mutations, including file-upload form submissions.
  const origin = request.headers.get('origin');
  if (origin && new URL(origin).host !== request.headers.get('host')) return NextResponse.json({ ok: false, error: 'Farklı kaynaktan aktarım engellendi.' }, { status: 403 });
  if (Number(request.headers.get('content-length') || 0) > MAX_BYTES + 65536) return NextResponse.json({ ok: false, error: 'Dosya en fazla 20 MB olabilir.' }, { status: 413 });
  try {
    if (process.env.APP_DATA_MODE !== 'original' && request.headers.get('content-type')?.includes('multipart/form-data')) {
      return NextResponse.json({ ok: false, error: 'Anonim sunumda dosya aktarımı kapalı. Asıl veriler korunuyor.' }, { status: 403 });
    }
    let payload: Record<string, unknown>;
    if (request.headers.get('content-type')?.includes('multipart/form-data')) {
      const form = await request.formData(); const file = form.get('file');
      if (!(file instanceof File) || !file.name.toLowerCase().endsWith('.csv')) throw new Error('Bir .csv dosyası seçin.');
      if (file.size > MAX_BYTES) throw new Error('Dosya en fazla 20 MB olabilir.');
      payload = { action: 'inspect', name: file.name, kind: form.get('kind'), encoding: form.get('encoding'), delimiter: form.get('delimiter') || undefined, file: Buffer.from(await file.arrayBuffer()).toString('base64') };
    } else {
      payload = await request.json();
      if (!['case_from_entity', 'case_list', 'case_detail', 'case_demo_prepare', 'case_evaluate', 'case_mutate', 'analyze', 'commit', 'report', 'export', 'schema', 'cockpit', 'signals', 'product_detail', 'stock_analysis', 'decision_catalog', 'decision_center', 'action_create', 'action_update', 'module_analytics', 'customer_analytics', 'customer_detail', 'pricing_analytics', 'seller_analytics', 'opportunity_analytics', 'forecasting_analytics', 'sales_profitability', 'executive_snapshot', 'unified_decision_center', 'signal_review', 'enhanced_action_update'].includes(String(payload.action))) throw new Error('Geçersiz işlem.');
    }
    return NextResponse.json(await engine(payload), { headers: { 'Cache-Control': 'no-store' } });
  } catch (e) { return NextResponse.json({ ok: false, error: (e as Error).message || 'İşlem tamamlanamadı.' }, { status: 400 }); }
}
