import { Injectable } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';

export interface SeoMetadata {
  title: string;
  description: string;
  keywords?: string;
  url?: string;
  image?: string;
}

@Injectable({
  providedIn: 'root',
})
export class SeoService {
  private readonly defaultImage = 'https://openclimatemap.org/favicon.png';
  private readonly baseUrl = 'https://openclimatemap.org';

  constructor(
    private meta: Meta,
    private titleService: Title,
  ) {}

  updateMetaTags(metadata: SeoMetadata): void {
    const fullUrl = metadata.url
      ? `${this.baseUrl}${metadata.url}`
      : this.baseUrl;
    const imageUrl = metadata.image || this.defaultImage;

    this.titleService.setTitle(metadata.title);

    this.meta.updateTag({ name: 'description', content: metadata.description });

    if (metadata.keywords) {
      this.meta.updateTag({ name: 'keywords', content: metadata.keywords });
    }

    this.meta.updateTag({ property: 'og:title', content: metadata.title });
    this.meta.updateTag({
      property: 'og:description',
      content: metadata.description,
    });
    this.meta.updateTag({ property: 'og:url', content: fullUrl });
    this.meta.updateTag({ property: 'og:image', content: imageUrl });

    this.meta.updateTag({ name: 'twitter:title', content: metadata.title });
    this.meta.updateTag({
      name: 'twitter:description',
      content: metadata.description,
    });
    this.meta.updateTag({ name: 'twitter:image', content: imageUrl });

    this.meta.updateTag({ rel: 'canonical', href: fullUrl });
  }

  setDefaultMetaTags(): void {
    this.updateMetaTags({
      title:
        'OpenClimateMap - Interactive Global Climate Maps | Temperature & Precipitation',
      description:
        'Explore historical and future global climate data, including temperature and precipitation changes based on CMIP6 climate scenarios. Explore interactive maps showing temperature trends and climate projections on a global map.',
      keywords:
        'climate map, temperature map, climate change, climate data, CMIP6, SSP scenarios, WorldClim, temperature projections, climate visualization, global warming',
      url: '/',
    });
  }
}
