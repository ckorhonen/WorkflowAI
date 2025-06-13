import { source } from '@/lib/source';
import {
  DocsPage,
  DocsBody,
  DocsDescription,
  DocsTitle,
} from 'fumadocs-ui/page';
import { notFound } from 'next/navigation';
import { createRelativeLink } from 'fumadocs-ui/mdx';
import type { MDXComponents } from 'mdx/types';
import { getMDXComponents } from '@/mdx-components';
import { getLLMText } from '@/lib/get-llm-text';
import { CopyMarkdownButton } from '@/components/copy-markdown-button';
import { Rate } from '@/components/rate';
import { sendFeedbackToSlack } from '@/app/actions/slack-feedback';
import { TOCDropdown } from '@/components/toc-dropdown';

export default async function Page(props: {
  params: Promise<{ slug?: string[] }>;
}) {
  const params = await props.params;
  const page = source.getPage(params.slug);
  if (!page) notFound();

  const MDXContent = page.data.body;
  
  // Generate LLM-friendly content
  const llmContent = await getLLMText(page);

  return (
    <DocsPage 
      toc={page.data.toc} 
      full={page.data.full}
      tableOfContent={{
        header: <TOCDropdown />
      }}
    >
      <div className="mb-4 flex items-center justify-between">
        <DocsTitle>{page.data.title}</DocsTitle>
        <CopyMarkdownButton content={llmContent} />
      </div>
      <DocsDescription>{page.data.description}</DocsDescription>
      <DocsBody>
        <MDXContent
          components={getMDXComponents({
            // this allows you to link to other pages with relative file paths
            a: createRelativeLink(source, page) as MDXComponents['a'],
          })}
        />
      </DocsBody>
      <Rate onRateAction={sendFeedbackToSlack} />
    </DocsPage>
  );
}

export async function generateStaticParams() {
  return source.generateParams();
}

export async function generateMetadata(props: {
  params: Promise<{ slug?: string[] }>;
}) {
  const params = await props.params;
  const page = source.getPage(params.slug);
  if (!page) notFound();

  return {
    title: page.data.title,
    description: page.data.description,
  };
}
