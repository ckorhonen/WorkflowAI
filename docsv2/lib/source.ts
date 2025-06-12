import { docs } from '@/.source';
import { loader } from 'fumadocs-core/source';
import { 
  BookOpen, 
  TestTube, 
  Plug, 
  BookMarked,
  FileText,
  Code,
  Sparkles,
  FileCode
} from 'lucide-react';
import { createElement } from 'react';

// Icon mapping
const icons: Record<string, React.ElementType> = {
  BookOpen,
  TestTube,
  Plug,
  BookMarked,
  FileText,
  Code,
  Sparkles,
  FileCode
};

// See https://fumadocs.vercel.app/docs/headless/source-api for more info
export const source = loader({
  // it assigns a URL to your pages
  baseUrl: '/docs',
  source: docs.toFumadocsSource(),
  icon(name) {
    if (!name || !(name in icons)) return undefined;
    const Icon = icons[name];
    return createElement(Icon);
  },
});
