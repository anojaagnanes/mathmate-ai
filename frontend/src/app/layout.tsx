import type { Metadata } from 'next';
import './globals.css';
import 'katex/dist/katex.min.css';
// JSXGraph's exports map excludes its stylesheet; resolve the installed asset directly.
import '../../node_modules/jsxgraph/distrib/jsxgraph.css';
import { Providers } from '@/components/providers';
export const metadata: Metadata = {title: 'MathMate AI · A little clarity. A lot of possibility.', description: 'Learn algebra with verified steps, visual graphs, and supportive practice.'};
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {return <html lang="en"><body><Providers>{children}</Providers></body></html>;}
