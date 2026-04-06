---
layout: page
title: Blog
permalink: /blog/
nav: true
nav_order: 6
description: Notes and posts from my Obsidian vault.
---

{% assign blog_entries = site.blog | sort: 'date' | reverse %}

{% if blog_entries.size > 0 %}
  <div class="news">
    {% for entry in blog_entries %}
      <div class="row mb-4">
        <div class="col-12">
          <h5 class="title font-weight-bold mb-1">
            <a href="{{ entry.url | relative_url }}">{{ entry.title }}</a>
          </h5>
          {% if entry.date %}
            <p class="post-meta mb-2">{{ entry.date | date: "%b %-d, %Y" }}</p>
          {% endif %}
          {% if entry.excerpt %}
            <p>{{ entry.excerpt | strip_html | truncate: 220 }}</p>
          {% endif %}
          <a class="post-link" href="{{ entry.url | relative_url }}">Read more</a>
        </div>
      </div>
    {% endfor %}
  </div>
{% else %}
  <p>No blog notes have been added yet. Put your Obsidian Markdown files in <a href="{{ '/_blog/' | relative_url }}">_blog</a> with front matter to make them appear here.</p>
{% endif %}
