import Document, { Html, Head, Main, NextScript } from "next/document";

class MyDocument extends Document {
  render() {
    return (
      <Html lang="en" className="notranslate" translate="no">
        <Head>
          {/* <link rel="manifest" href="/manifest.json"></link> */}
          <link rel="apple-touch-icon" href="/icon.png"></link>
          <meta name="theme-color" content="#fff" />
        </Head>
        <body>
          <Main />
          <div id="popup"></div>
          <div id="createcrawl"></div>
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
