import type { Metadata, Viewport } from 'next';
import './globals.css';
import './ui-refinements.css';
import 'katex/dist/katex.min.css';
// JSXGraph's exports map excludes its stylesheet; resolve the installed asset directly.
import '../../node_modules/jsxgraph/distrib/jsxgraph.css';
import './magical-theme.css';
import './responsive.css';
import { Providers } from '@/components/providers';
export const metadata: Metadata = {title: 'MathMate AI · A little clarity. A lot of possibility.', description: 'Learn algebra with verified steps, visual graphs, and supportive practice.'};
export const viewport: Viewport = {width: 'device-width', initialScale: 1};
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {return <html lang="en"><body><link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/><link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Caveat:wght@500;600;700&display=swap" rel="stylesheet"/><Providers>{children}</Providers></body></html>;}
