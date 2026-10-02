import type { Metadata } from 'next';
import Script from 'next/script';
import './globals.css';
import './acceptance.css';
import './nav-theme.css';
export const dynamic = 'force-dynamic';
export const metadata: Metadata = { title: 'Ticari Öngörü · Veriden ölçülen sonuca', description: 'Kanıtlı içgörüler, kullanıcı onayı, aksiyon takibi ve ticari geri bildirim.' };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <head>
        <Script
          id="anti-extension-guard"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                function cleanExtensionAttributes(node) {
                  if (!node || node.nodeType !== 1) return;
                  if (node.hasAttribute('bis_skin_checked')) node.removeAttribute('bis_skin_checked');
                  if (node.hasAttribute('bis_register')) node.removeAttribute('bis_register');
                  const children = node.querySelectorAll ? node.querySelectorAll('[bis_skin_checked], [bis_register]') : [];
                  for (let i = 0; i < children.length; i++) {
                    children[i].removeAttribute('bis_skin_checked');
                    children[i].removeAttribute('bis_register');
                  }
                }

                try {
                  cleanExtensionAttributes(document.documentElement);
                  const observer = new MutationObserver(function(mutations) {
                    for (let i = 0; i < mutations.length; i++) {
                      const m = mutations[i];
                      if (m.type === 'attributes') {
                        if (m.attributeName === 'bis_skin_checked' || m.attributeName === 'bis_register') {
                          m.target.removeAttribute(m.attributeName);
                        }
                      } else if (m.type === 'childList') {
                        for (let j = 0; j < m.addedNodes.length; j++) {
                          cleanExtensionAttributes(m.addedNodes[j]);
                        }
                      }
                    }
                  });
                  observer.observe(document.documentElement, { attributes: true, subtree: true, childList: true, attributeFilter: ['bis_skin_checked', 'bis_register'] });
                } catch(e) {}

                // Next.js overlay uyarısını eklenti öznitelikleri için filtrele
                const origError = console.error;
                console.error = function(...args) {
                  const msg = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].message ? args[0].message : '');
                  if (msg && (msg.includes('bis_skin_checked') || msg.includes('bis_register') || (msg.includes('hydration') && msg.includes('bis_')))) {
                    return;
                  }
                  origError.apply(console, args);
                };
              })();
            `,
          }}
        />
      </head>
      <body suppressHydrationWarning className={process.env.APP_DATA_MODE !== 'original' ? 'anonymous-presentation' : undefined}>
        {process.env.APP_DATA_MODE !== 'original' && (
          <aside className="privacy-notice" aria-label="Veri gizliliği">
            <strong>Anonim sunum</strong>
            <span>İsimler, tarihler, satış tutarları ve stok miktarları örnektir. Asıl veriler korunuyor.</span>
          </aside>
        )}
        {children}
      </body>
    </html>
  );
}
