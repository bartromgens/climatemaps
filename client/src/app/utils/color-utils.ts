export class ColorUtils {
  static intensifyColor(color: string, darkenFactor: number): string {
    if (!color) {
      return '#000000';
    }

    const hexMatch = color.match(/^#([0-9a-f]{6})$/i);
    if (hexMatch) {
      const r = parseInt(hexMatch[1].substring(0, 2), 16);
      const g = parseInt(hexMatch[1].substring(2, 4), 16);
      const b = parseInt(hexMatch[1].substring(4, 6), 16);

      const newR = Math.max(0, Math.floor(r * (1 - darkenFactor)));
      const newG = Math.max(0, Math.floor(g * (1 - darkenFactor)));
      const newB = Math.max(0, Math.floor(b * (1 - darkenFactor)));

      return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
    }

    const rgbMatch = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/i);
    if (rgbMatch) {
      const r = parseInt(rgbMatch[1], 10);
      const g = parseInt(rgbMatch[2], 10);
      const b = parseInt(rgbMatch[3], 10);

      const newR = Math.max(0, Math.floor(r * (1 - darkenFactor)));
      const newG = Math.max(0, Math.floor(g * (1 - darkenFactor)));
      const newB = Math.max(0, Math.floor(b * (1 - darkenFactor)));

      return `rgb(${newR}, ${newG}, ${newB})`;
    }

    return color;
  }
}
