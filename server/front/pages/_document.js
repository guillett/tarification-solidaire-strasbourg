import { Html, Head, Main, NextScript } from 'next/document'
import Script from 'next/script'

export default function Document() {
  return (
    <Html>
      <Head />
      <body>
        <Main />
        <NextScript />
        <Script
          src="https://grist.incubateur.net/grist-plugin-api.js"
          strategy="beforeInteractive"
          async=""
        />
      </body>
    </Html>
  )
}
