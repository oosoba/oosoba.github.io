---
title: Example Post: How Writing Works Here
date: 2026-07-01
summary: A throwaway example showing Markdown, code highlighting, math, and tags. Delete or replace it.
tags: [meta, example]
draft: false
---

This is an example post. It exists to show what the blog pipeline supports. Delete this file (`posts/2026-07-01-example-post.md`) or replace it with your own.

## Writing a post

Each post is a Markdown file in `posts/`, named `YYYY-MM-DD-slug.md`, with a small front-matter block at the top:

```yaml
---
title: My Post Title
date: 2026-07-15
summary: One-line teaser for the index.
tags: [governance, ai]
draft: false
---
```

Run `python build.py` and the post is rendered to `writing/<slug>.html`, with an entry added to the **Writing** tab. Set `draft: true` to keep a post out of the build.

## Code

Fenced code blocks are highlighted at build time, so there is no client-side highlighter to load:

```python
def noisy_em(theta, data, noise_scale):
    """One NEM step: inject annealed noise into the E-step."""
    n = sample_noise(scale=noise_scale)
    return m_step(e_step(theta, data + n))
```

Inline `code` works too.

## Math

Inline math renders with KaTeX, for example \(p(R \mid S, G)\) over demographic groups. Display math is also supported:

$$
\mathbb{E}_{q}\!\left[\log p(x, z)\right] - \mathbb{E}_{q}\!\left[\log q(z)\right] \;=\; \log p(x) - \mathrm{KL}\!\left(q \,\|\, p(z \mid x)\right).
$$

> Math is loaded only on post pages, so the rest of the site stays light.

## Tags

The tags in the front matter become filter chips on the Writing tab, so readers can narrow to a topic. Tags are display-and-filter only; there are no separate per-tag pages.
