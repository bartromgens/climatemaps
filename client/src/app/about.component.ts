import { Component, OnInit } from '@angular/core';
import { SeoService } from './core/seo.service';

@Component({
  selector: 'app-about',
  standalone: true,
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.scss'],
})
export class AboutComponent implements OnInit {
  constructor(private seoService: SeoService) {}

  ngOnInit(): void {
    this.seoService.updateMetaTags({
      title: 'About OpenClimateMap - Climate Data Visualization Platform',
      description:
        'Learn about OpenClimateMap, an open-source platform for visualizing global climate data including historical observations and CMIP6 future projections. Free climate maps for researchers, educators, and policy makers.',
      keywords:
        'about OpenClimateMap, climate data source, CMIP6, WorldClim, climate visualization, open source climate tool, climate research',
      url: '/about',
    });
  }
}
