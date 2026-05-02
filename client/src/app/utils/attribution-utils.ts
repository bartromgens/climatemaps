export const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';

export function getDataAttribution(source: string | null | undefined): string {
  if (!source) {
    return '';
  }

  const parts: string[] = [];

  if (source.includes('worldclim.org')) {
    parts.push(
      '<a href="https://www.worldclim.org/" target="_blank" rel="noopener">WorldClim</a>',
    );
  }

  if (source.includes('chelsa-climate.org')) {
    parts.push(
      '<a href="https://www.chelsa-climate.org/" target="_blank" rel="noopener">CHELSA</a>',
    );
  }

  if (parts.length === 0) {
    return '';
  }

  return `Data: ${parts.join(' &amp; ')}`;
}
