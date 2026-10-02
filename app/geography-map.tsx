'use client';

import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import './research-advanced.css';

type Row = Record<string, string | number | null | undefined>;
type Country = {
  code: string;
  name: string;
  aliases?: string[];
  geometry: { type: string; coordinates: number[][][] | number[][][][] };
};

type Region = {
  country: string;
  name: string;
  code: string;
  geometry: { type: string; coordinates: number[][][] | number[][][][] };
};

type RegionData = Region & {
  sales: number;
  profit: number;
  margin: number | null;
  returns: number;
  customers: number;
  cities: Row[];
  center: [number, number];
  path: string;
};

type CityPoint = {
  name: string;
  city: string;
  country: string;
  regionName: string;
  sales: number;
  profit: number;
  customers: number;
  invoices: number;
  returns: number;
  lat: number;
  lon: number;
  px: number;
  py: number;
};

const money = (n: number) => n.toLocaleString('tr-TR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
const number = (n: number, d = 1) => n.toLocaleString('tr-TR', { maximumFractionDigits: d });

// Şehir / Departman Performans Renk Skalası (Zümrüt Yeşil & Jade Eşikler)
const REGION_EMERALD_PALETTE = [
  '#a7f3d0', // 1. Kademe: Düşük / Başlangıç (<€20K)
  '#6ee7b7', // 2. Kademe: Gelişen Şehir (€20K - €50K)
  '#34d399', // 3. Kademe: Orta Hacim (€50K - €100K)
  '#10b981', // 4. Kademe: Güçlü Şehir Havzası (€100K - €200K)
  '#059669', // 5. Kademe: Yüksek Hacim (€200K - €300K)
  '#047857', // 6. Kademe: Zirve Ticari Merkez (€300K+ Strazburg, Müluz)
];

const RETURN_PALETTE = [
  '#10b981', // Düşük İade
  '#38bdf8',
  '#fbbf24',
  '#f97316',
  '#ef4444',
  '#991b1b', // Yüksek İade
];

// Dünya Görünümünde Ülke Renk Skalası (Makro Kloroplet)
const COUNTRY_CHOROPLETH_PALETTE = [
  '#d1fae5', // Açık yeşil
  '#a7f3d0',
  '#34d399',
  '#10b981',
  '#059669',
  '#047857', // En yüksek ciro
];

const COUNTRY_CENTROIDS: Record<string, { lat: number; lon: number; name: string }> = {
  FRA: { lat: 46.8, lon: 2.8, name: 'Fransa' },
  DEU: { lat: 51.2, lon: 10.4, name: 'Almanya' },
  BEL: { lat: 50.8, lon: 4.4, name: 'Belçika' },
  LUX: { lat: 49.8, lon: 6.1, name: 'Lüksemburg' },
  TUR: { lat: 39.1, lon: 35.2, name: 'Türkiye' },
  NLD: { lat: 52.2, lon: 5.3, name: 'Hollanda' },
  AUT: { lat: 47.5, lon: 14.5, name: 'Avusturya' },
  CHE: { lat: 46.8, lon: 8.2, name: 'İsviçre' },
  GBR: { lat: 54.0, lon: -2.5, name: 'Birleşik Krallık' },
  ITA: { lat: 42.8, lon: 12.8, name: 'İtalya' },
  ESP: { lat: 40.4, lon: -3.7, name: 'İspanya' },
};

// Eksik koordinatları telafi eden coğrafi sözlük
const FALLBACK_CITY_COORDS: Record<string, [number, number]> = {
  'metz': [49.1193, 6.1757],
  'freiburg': [47.9990, 7.8421],
  'saint-louis': [47.5858, 7.5628],
  'anjoutey': [47.7011, 6.9317],
  'vandouvre-les-nancy': [48.6583, 6.1667],
  'bad-sackingen': [47.5500, 7.9500],
  'neuenburg': [47.8139, 7.5583],
  'jarville la malgrane': [48.6692, 6.2081],
  'schweighouse sur mod': [48.8167, 7.7333],
  'appenweier': [48.5333, 7.9833],
  'marseille': [43.2965, 5.3698],
  'brussels': [50.8503, 4.3517],
  'brussel': [50.8503, 4.3517],
  'bruxelles': [50.8503, 4.3517],
  'strasbourg': [48.5839, 7.7455],
  'mulhouse': [47.7520, 7.3287],
  'colmar': [48.0808, 7.3558],
  'pfastatt': [47.7692, 7.3030],
  'weil am rhein': [47.5900, 7.6200],
  'lahr': [48.3400, 7.9500],
  'kehl': [48.5700, 7.8100],
  'offenburg': [48.4700, 7.9400],
  'belfort': [47.6397, 6.8638],
  'epinal': [48.1744, 6.4497],
  'nancy': [48.6921, 6.1844],
  'stuttgart': [48.7758, 9.1829],
  'rastatt': [48.8587, 8.2043],
  'pontarlier': [46.9061, 6.3547],
  'pforzheim': [48.8932, 8.6987],
  'esch sur azette': [49.4958, 5.9806],
  'esch-sur-alzette': [49.4958, 5.9806],
};

export const TURKISH_CITIES: Record<string, string> = {
  'Strasbourg': 'Strazburg',
  'Brussel': 'Brüksel',
  'Bruxelles': 'Brüksel',
  'Brussels': 'Brüksel',
  'Marseille': 'Marsilya',
  'Colmar': 'Kolmar',
  'Mulhouse': 'Müluz',
  'Freiburg': 'Frayburg',
  'München': 'Münih',
  'Munich': 'Münih',
  'Köln': 'Köln',
  'Cologne': 'Köln',
  'Nürnberg': 'Nürnberg',
  'Frankfurt am Main': 'Frankfurt',
  'Frankfurt': 'Frankfurt',
  'Wien': 'Viyana',
  'Zürich': 'Zürih',
  'Paris': 'Paris',
  'Achern': 'Achern',
  'Anjoutey': 'Anjoutey',
  'Appenweier': 'Appenweier',
  'Auboué': 'Auboué',
  'Audincourt': 'Audincourt',
  'Bad Krozingen': 'Bad Krozingen',
  'Bad-Sackingen': 'Bad Säckingen',
  'Belfort': 'Belfort',
  'Bischheim': 'Bischheim',
  'Bischwiller': 'Bischwiller',
  'Boulay Moselle': 'Boulay-Moselle',
  'Bühl': 'Bühl',
  'Eckbolsheim': 'Eckbolsheim',
  'Erstein': 'Erstein',
  'Esch Sur Azette': 'Esch-sur-Alzette',
  'Forbach': 'Forbach',
  'Haguenau': 'Haguenau',
  'Heilbronn- Böckingen': 'Heilbronn',
  'Illkirch': 'Illkirch',
  'Illzach': 'Illzach',
  'Kehl': 'Kehl',
  'Kingersheim': 'Kingersheim',
  'Lahr': 'Lahr',
  'Lörrach': 'Lörrach',
  'Metz': 'Metz',
  'Offenburg': 'Offenburg',
  'Ostwald': 'Ostwald',
  'Pfastatt': 'Pfastatt',
  'Pontarlier': 'Pontarlier',
  'Pforzheim': 'Pforzheim',
  'Rastatt': 'Rastatt',
  'Rheinfelden': 'Rheinfelden',
  'Saint-Louis': 'Saint-Louis',
  'Saverne': 'Saverne',
  'Schiltigheim': 'Schiltigheim',
  'Sélestat': 'Sélestat',
  'Stuttgart': 'Stuttgart',
  'Thann': 'Thann',
  'Weil Am Rhein': 'Weil am Rhein',
  'Wittenheim': 'Wittenheim',
  'Woippy': 'Woippy',
  'Vandouvre-Les-Nancy': 'Nancy (Vandœuvre)',
  'Épinal': 'Epinal',
};

export const TURKISH_COUNTRIES: Record<string, string> = {
  'FRA': 'Fransa',
  'Frankreich': 'Fransa',
  'France': 'Fransa',
  'DEU': 'Almanya',
  'Deutschland': 'Almanya',
  'Germany': 'Almanya',
  'BEL': 'Belçika',
  'Belgien': 'Belçika',
  'LUX': 'Lüksemburg',
  'CHE': 'İsviçre',
  'AUT': 'Avusturya',
  'TUR': 'Türkiye',
  'NLD': 'Hollanda',
  'GBR': 'Birleşik Krallık',
  'ITA': 'İtalya',
  'ESP': 'İspanya',
  'GUF': 'Fransız Guyanası',
  'Bilinmiyor': 'Diğer / Tanımsız',
};

export const TURKISH_REGIONS: Record<string, string> = {
  'Bas-Rhin': 'Strazburg ve Çevresi (Aşağı Ren)',
  'Haut-Rhin': 'Müluz / Kolmar (Yukarı Ren)',
  'Moselle': 'Metz ve Mozel Havzası',
  'Meurthe-et-Moselle': 'Nancy ve Çevresi',
  'Bouches-du-Rhône': 'Marsilya ve Rhône Deltası',
  'Doubs': 'Besançon ve Pontarlier',
  'Vosges': 'Epinal ve Vojlar',
  'Territoire de Belfort': 'Belfort Bölgesi',
  'Ortenaukreis': 'Ortenau (Offenburg / Lahr)',
  'Rastatt': 'Rastatt ve Çevresi',
  'Breisgau-Hochschwarzwald': 'Frayburg ve Breisgau',
  'Lörrach': 'Lörrach ve Weil am Rhein',
  'Belçika': 'Brüksel Başkent Bölgesi',
  'Lüksemburg': 'Lüksemburg',
};

export const trCountry = (c: string) => TURKISH_COUNTRIES[c] || c;
export const trCity = (c: any) => TURKISH_CITIES[String(c || '').trim()] || String(c || '');
export const trRegion = (r: string) => TURKISH_REGIONS[r] || r;

function getRegionCityLabel(reg: RegionData): string {
  const regName = String(reg.name || '');
  if (regName === 'Bas-Rhin') return 'Strazburg Havzası';
  if (regName === 'Haut-Rhin') return 'Müluz / Kolmar';
  if (regName === 'Moselle') return 'Metz';
  if (regName === 'Meurthe-et-Moselle') return 'Nancy';
  if (regName === 'Bouches-du-Rhône') return 'Marsilya';
  if (regName === 'Doubs') return 'Pontarlier / Doubs';
  if (regName === 'Vosges') return 'Epinal';
  if (regName === 'Territoire de Belfort') return 'Belfort';
  if (regName === 'Ortenaukreis') return 'Lahr / Offenburg';
  if (regName === 'Lörrach') return 'Weil am Rhein / Lörrach';
  if (regName === 'Belçika' || regName === 'Belgien') return 'Brüksel';
  if (regName === 'Lüksemburg') return 'Lüksemburg';
  return trRegion(regName);
}

// Ray-casting point-in-polygon
function isPointInRing(pt: [number, number], ring: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1];
    const xj = ring[j][0], yj = ring[j][1];
    const intersect = yi > pt[1] !== yj > pt[1] && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

// Web Mercator Projeksiyonu
function projectMercator(lon: number, lat: number): [number, number] {
  const x = lon + 180;
  const clampedLat = Math.max(-84, Math.min(84, lat));
  const rad = (clampedLat * Math.PI) / 180;
  const y = 90 - (180 / Math.PI) * Math.log(Math.tan(Math.PI / 4 + rad / 2));
  return [x, y];
}

function getPolyPath(geometry: { type: string; coordinates: number[][][] | number[][][][] }) {
  const polys = geometry.type === 'Polygon'
    ? [geometry.coordinates as number[][][]]
    : (geometry.coordinates as number[][][][]);
  return polys
    .map(poly =>
      poly
        .map(ring =>
          ring
            .map(([lon, lat], i) => {
              const [px, py] = projectMercator(lon, lat);
              return `${i ? 'L' : 'M'}${px.toFixed(2)},${py.toFixed(2)}`;
            })
            .join(' ') + 'Z'
        )
        .join(' ')
    )
    .join(' ');
}

function getCentroid(geometry: { type: string; coordinates: number[][][] | number[][][][] }): [number, number] {
  const polys = geometry.type === 'Polygon'
    ? [geometry.coordinates as number[][][]]
    : (geometry.coordinates as number[][][][]);
  let totalLon = 0, totalLat = 0, count = 0;
  for (const poly of polys) {
    const ring = poly[0];
    if (!ring) continue;
    for (const [lon, lat] of ring) {
      totalLon += lon;
      totalLat += lat;
      count++;
    }
  }
  return count > 0 ? [totalLon / count, totalLat / count] : [0, 0];
}

export default function GeographyMap({
  rows,
  onFilter,
}: {
  rows: Row[];
  onFilter: (country: string, city?: string, cityList?: string[]) => void;
}) {
  const [world, setWorld] = useState<Country[]>([]);
  const [rawRegions, setRawRegions] = useState<Region[]>([]);
  const [metric, setMetric] = useState<'sales' | 'profit' | 'margin' | 'customers' | 'returns'>('sales');
  const [country, setCountry] = useState<string>('');
  const [selectedRegion, setSelectedRegion] = useState<RegionData | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<CityPoint | null>(null);
  const [hoveredRegion, setHoveredRegion] = useState<RegionData | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<CityPoint | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Başlangıç Görünümü: Avrupa Ticaret Havzası (Fransa, Almanya, Belçika ekseni)
  // X: 173, Y: 26, W: 24, H: 16
  const [view, setView] = useState<{ x: number; y: number; w: number; h: number }>({
    x: 173,
    y: 26,
    w: 24,
    h: 16,
  });

  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<{ x: number; y: number; vx: number; vy: number; moved: boolean } | null>(null);

  // 1. Sınır Dosyalarını Yükle
  useEffect(() => {
    let live = true;
    Promise.all([
      fetch('/maps/world.json').then(r => r.json()),
      fetch('/maps/regions.json').then(r => r.json()),
    ])
      .then(([wData, rData]) => {
        if (live) {
          setWorld(wData);
          setRawRegions(rData);
        }
      })
      .catch(() => {
        if (live) setError('Harita sınır dosyaları yüklenemedi.');
      });
    return () => {
      live = false;
    };
  }, []);

  const worldPaths = useMemo(() => world.map(c => ({ ...c, path: getPolyPath(c.geometry) })), [world]);

  // 2. KULLANICI KURALI: "eğer o şehirde birden fazla alıcı varsa onlar toplanmalı"
  // Şehir/İl Poligonlarına Eşleme ve Alıcıların Toplanması
  const regionsData = useMemo(() => {
    if (!rawRegions.length) return [];

    const map = new Map<string, RegionData>();
    for (const reg of rawRegions) {
      const key = `${reg.country}-${reg.code || reg.name}`;
      map.set(key, {
        ...reg,
        sales: 0,
        profit: 0,
        margin: null,
        returns: 0,
        customers: 0,
        cities: [],
        center: getCentroid(reg.geometry),
        path: getPolyPath(reg.geometry),
      });
    }

    for (const r of rows) {
      const cityName = String(r.city || '').trim();
      let lat = r.latitude != null ? Number(r.latitude) : null;
      let lon = r.longitude != null ? Number(r.longitude) : null;

      if ((!lat || !lon) && FALLBACK_CITY_COORDS[cityName.toLowerCase()]) {
        [lat, lon] = FALLBACK_CITY_COORDS[cityName.toLowerCase()];
      }

      if (!lat || !lon || !r.countryCode) continue;
      const pt: [number, number] = [lon, lat];
      const cCode = String(r.countryCode);

      let matchedRegion: RegionData | null = null;
      for (const reg of map.values()) {
        if (reg.country !== cCode) continue;
        const geom = reg.geometry;
        const polys = geom.type === 'Polygon' ? [geom.coordinates as number[][][]] : (geom.coordinates as number[][][][]);
        for (const poly of polys) {
          if (poly[0] && isPointInRing(pt, poly[0])) {
            matchedRegion = reg;
            break;
          }
        }
        if (matchedRegion) break;
      }

      if (matchedRegion) {
        matchedRegion.sales += Number(r.sales || 0);
        matchedRegion.profit += Number(r.profit || 0);
        matchedRegion.returns += Number(r.returns || 0);
        // O şehirdeki/ildeki birden fazla alıcı toplanır:
        matchedRegion.customers += Number(r.customers || 0);
        matchedRegion.cities.push({
          ...r,
          latitude: lat,
          longitude: lon,
        });
      }
    }

    for (const reg of map.values()) {
      reg.margin = reg.sales ? (reg.profit / reg.sales) * 100 : null;
    }

    return Array.from(map.values());
  }, [rawRegions, rows]);

  // Sadece satışı olan aktif şehir/il departmanları
  const activeRegions = useMemo(() => {
    return regionsData.filter(r => r.sales > 0);
  }, [regionsData]);

  // 3. Ülke Kümülatif Toplamları
  const countryTotals = useMemo(() => {
    const map = new Map<string, { country: string; code: string; sales: number; profit: number; margin: number | null; customers: number; returns: number }>();
    for (const r of rows) {
      if (!r.countryCode) continue;
      const c = String(r.countryCode);
      const cur = map.get(c) || { country: trCountry(String(r.country || c)), code: c, sales: 0, profit: 0, margin: null, customers: 0, returns: 0 };
      cur.sales += Number(r.sales || 0);
      cur.profit += Number(r.profit || 0);
      cur.returns += Number(r.returns || 0);
      cur.customers += Number(r.customers || 0);
      map.set(c, cur);
    }
    for (const cur of map.values()) {
      cur.margin = cur.sales ? (cur.profit / cur.sales) * 100 : null;
    }
    return map;
  }, [rows]);

  const getVal = useCallback(
    (item: { sales: number; profit: number; margin: number | null; customers: number; returns: number } | null | undefined) => {
      if (!item) return 0;
      return Number(item[metric] || 0);
    },
    [metric]
  );

  // Şehir / İl Bölge Renk Skalası Eşiği
  const maxRegionVal = useMemo(() => {
    const vals = activeRegions.map(r => getVal(r)).filter(v => v > 0);
    return vals.length ? Math.max(...vals) : 1;
  }, [activeRegions, getVal]);

  const getRegionColor = useCallback(
    (val: number | null | undefined) => {
      if (val == null || val <= 0) return '#ffffff';
      const colors = metric === 'returns' ? RETURN_PALETTE : REGION_EMERALD_PALETTE;
      if (metric === 'sales') {
        if (val < 20000) return colors[0];
        if (val < 50000) return colors[1];
        if (val < 100000) return colors[2];
        if (val < 200000) return colors[3];
        if (val < 300000) return colors[4];
        return colors[5];
      }
      if (val < maxRegionVal * 0.12) return colors[0];
      if (val < maxRegionVal * 0.28) return colors[1];
      if (val < maxRegionVal * 0.48) return colors[2];
      if (val < maxRegionVal * 0.70) return colors[3];
      if (val < maxRegionVal * 0.88) return colors[4];
      return colors[5];
    },
    [maxRegionVal, metric]
  );

  // Ülkeler için kloroplet renk skalası (Çok uzaklaştırıldığında)
  const maxCountryVal = useMemo(() => {
    const vals = Array.from(countryTotals.values()).map(c => getVal(c)).filter(v => v > 0);
    return vals.length ? Math.max(...vals) : 1;
  }, [countryTotals, getVal]);

  const getCountryColor = useCallback(
    (val: number | null | undefined) => {
      if (val == null || val <= 0) return '#ffffff';
      const colors = metric === 'returns' ? RETURN_PALETTE : COUNTRY_CHOROPLETH_PALETTE;
      if (val < maxCountryVal * 0.10) return colors[0];
      if (val < maxCountryVal * 0.25) return colors[1];
      if (val < maxCountryVal * 0.50) return colors[2];
      if (val < maxCountryVal * 0.75) return colors[3];
      if (val < maxCountryVal * 0.90) return colors[4];
      return colors[5];
    },
    [maxCountryVal, metric]
  );

  const formatDisplay = useCallback(
    (val: number | null | undefined) => {
      if (val == null || val === 0) return 'İşlem Yok';
      if (metric === 'margin') return `%${number(val, 1)}`;
      if (metric === 'customers') return `${number(val, 0)} Alıcı`;
      return money(val);
    },
    [metric]
  );

  // KULLANICI KURALI VE 3 KADEMELİ DİNAMİK SEVİYE:
  // 1. Çok uzaklaştırılırsa ülkeler boyansın: isCountryLevel (view.w >= 26)
  // 2. Yeterince büyütülüp şehir boyutuna gelirse noktalar gelsin: isCityZoomLevel (view.w < 6.5 veya seçili şehir varsa)
  // 3. Onun dışında şehirler (iller/departmanlar) boyansın: isRegionLevel
  const isCountryLevel = view.w >= 26;
  const isCityZoomLevel = view.w < 6.5 || selectedRegion !== null;

  // Zoom ve Pan
  const zoom = useCallback((factor: number, cx?: number, cy?: number) => {
    setView(v => {
      const nextW = Math.max(1.5, Math.min(360, v.w * factor));
      const nextH = Math.max(1.0, Math.min(180, v.h * factor));
      const focusX = cx != null ? cx : v.x + v.w / 2;
      const focusY = cy != null ? cy : v.y + v.h / 2;
      const ratioX = (focusX - v.x) / v.w;
      const ratioY = (focusY - v.y) / v.h;
      return {
        x: Math.max(0, Math.min(360 - nextW, focusX - ratioX * nextW)),
        y: Math.max(0, Math.min(180 - nextH, focusY - ratioY * nextH)),
        w: nextW,
        h: nextH,
      };
    });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const clientY = e.clientY - rect.top;

      setView(v => {
        const mouseX = v.x + (clientX / rect.width) * v.w;
        const mouseY = v.y + (clientY / rect.height) * v.h;
        const factor = e.deltaY < 0 ? 0.82 : 1.22;
        const nextW = Math.max(1.5, Math.min(360, v.w * factor));
        const nextH = Math.max(1.0, Math.min(180, v.h * factor));
        const ratioX = clientX / rect.width;
        const ratioY = clientY / rect.height;

        return {
          x: Math.max(0, Math.min(360 - nextW, mouseX - ratioX * nextW)),
          y: Math.max(0, Math.min(180 - nextH, mouseY - ratioY * nextH)),
          w: nextW,
          h: nextH,
        };
      });
    };

    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, []);

  // Hızlı Ticaret Havzası Odakları
  const focusRhineCorridor = useCallback(() => {
    setCountry('');
    setSelectedRegion(null);
    setSelectedPoint(null);
    onFilter('');
    setView({ x: 184.2, y: 33.2, w: 7.2, h: 4.8 });
  }, [onFilter]);

  const focusEuropeBasin = useCallback(() => {
    setCountry('');
    setSelectedRegion(null);
    setSelectedPoint(null);
    onFilter('');
    setView({ x: 174, y: 27, w: 22, h: 14.6 });
  }, [onFilter]);

  const focusWorld = useCallback(() => {
    setCountry('');
    setSelectedRegion(null);
    setSelectedPoint(null);
    onFilter('');
    setView({ x: 155, y: 16, w: 58, h: 36 });
  }, [onFilter]);

  const focusCountry = useCallback(
    (cCode: string) => {
      setCountry(cCode);
      setSelectedRegion(null);
      setSelectedPoint(null);
      const entry = rows.find(r => r.countryCode === cCode);
      onFilter(entry ? String(entry.country) : '');

      if (!cCode) {
        focusEuropeBasin();
        return;
      }

      const cRegions = activeRegions.filter(r => r.country === cCode);
      if (cRegions.length) {
        const pts = cRegions.map(r => projectMercator(r.center[0], r.center[1]));
        const xs = pts.map(p => p[0]);
        const ys = pts.map(p => p[1]);
        const minX = Math.min(...xs), maxX = Math.max(...xs);
        const minY = Math.min(...ys), maxY = Math.max(...ys);
        const spanW = Math.max(5, (maxX - minX) * 1.5);
        const spanH = Math.max(3.5, (maxY - minY) * 1.5);
        const w = Math.min(360, Math.max(spanW, spanH * 1.6));
        const h = w / 1.6;
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        setView({
          x: Math.max(0, Math.min(360 - w, cx - w / 2)),
          y: Math.max(0, Math.min(180 - h, cy - h / 2)),
          w,
          h,
        });
      }
    },
    [rows, activeRegions, onFilter, focusEuropeBasin]
  );

  // Şehir boyutuna gelindiğinde gösterilecek Bireysel Alıcı/Lokasyon Noktaları
  const localCityPoints = useMemo(() => {
    if (!isCityZoomLevel) return [];

    const points: CityPoint[] = [];
    const sourceRegions = selectedRegion ? [selectedRegion] : activeRegions;

    for (const reg of sourceRegions) {
      for (const r of reg.cities) {
        const cityName = String(r.city || '').trim();
        const lat = Number(r.latitude);
        const lon = Number(r.longitude);
        if (!lat || !lon) continue;

        const [px, py] = projectMercator(lon, lat);

        // Viewport içinde mi?
        if (px >= view.x - 1 && px <= view.x + view.w + 1 && py >= view.y - 1 && py <= view.y + view.h + 1) {
          points.push({
            name: trCity(cityName),
            city: cityName,
            country: String(r.countryCode || reg.country),
            regionName: getRegionCityLabel(reg),
            sales: Number(r.sales || 0),
            profit: Number(r.profit || 0),
            customers: Number(r.customers || 1),
            invoices: Number(r.invoices || 1),
            returns: Number(r.returns || 0),
            lat,
            lon,
            px,
            py,
          });
        }
      }
    }

    return points.sort((a, b) => b.sales - a.sales);
  }, [isCityZoomLevel, selectedRegion, activeRegions, view]);

  // Şehir seviyesinde gösterilecek temiz rozetler (Collision avoidance)
  const regionBadges = useMemo(() => {
    if (isCountryLevel || isCityZoomLevel) return [];

    const placed: { reg: RegionData; cx: number; cy: number; label: string; valStr: string; custStr: string; badgeW: number; badgeH: number; fontSz: number }[] = [];

    const sorted = [...activeRegions].sort((a, b) => b.sales - a.sales);

    for (const reg of sorted) {
      const [cx, cy] = projectMercator(reg.center[0], reg.center[1]);
      if (cx < view.x || cx > view.x + view.w || cy < view.y || cy > view.y + view.h) continue;

      const fontSz = Math.max(0.12, Math.min(0.24, view.w * 0.016));
      const label = getRegionCityLabel(reg);
      const valStr = formatDisplay(getVal(reg));
      const custStr = `${reg.customers} Alıcı`;
      // Rozet genişliği: İki metin (etiket ve tutar) yan yana
      const badgeW = (label.length + valStr.length) * fontSz * 0.58 + fontSz * 3.4;
      const badgeH = fontSz * 2.2;

      // Gerçek dikdörtgen kutu çakışma testi (Kutu genişliği + dikey güvenlik payı)
      const collides = placed.some(
        p => Math.abs(p.cx - cx) < (p.badgeW + badgeW) * 0.52 + 0.1 && Math.abs(p.cy - cy) < (p.badgeH + badgeH) * 0.55 + 0.08
      );
      if (collides) continue;

      placed.push({ reg, cx, cy, label, valStr, custStr, badgeW, badgeH, fontSz });
    }

    return placed;
  }, [isCountryLevel, isCityZoomLevel, activeRegions, view, formatDisplay, getVal]);

  // KULLANICI KURALI: "böyle kocaman noktalar yerine ülkelerin sınırları içerisinde ülkeler boyansın"
  // Çok uzakta gösterilecek minimalist ülke etiketleri (KUTUSUZ, harita dokusuna gömülü)
  const worldCountryLabels = useMemo(() => {
    if (!isCountryLevel) return [];
    const list: { code: string; name: string; valStr: string; cx: number; cy: number; fontSz: number }[] = [];
    for (const [code, cTotal] of countryTotals.entries()) {
      if (cTotal.sales <= 0) continue;
      // Çok küçük ülkeleri (Lüksemburg gibi) makro ölçekte harita yazısıyla boğma; hover ile göster
      if (code === 'LUX' && view.w > 30) continue;

      const centroid = COUNTRY_CENTROIDS[code];
      if (!centroid) continue;
      const [cx, cy] = projectMercator(centroid.lon, centroid.lat);

      const fontSz = Math.max(0.42, Math.min(0.95, view.w * 0.013));
      const val = getVal(cTotal);
      const compactVal = val >= 1000000
        ? `€${(val / 1000000).toFixed(2)}M`
        : val >= 1000
        ? `€${Math.round(val / 1000)}K`
        : money(val);

      list.push({
        code,
        name: centroid.name,
        valStr: compactVal,
        cx,
        cy,
        fontSz,
      });
    }
    return list;
  }, [countryTotals, isCountryLevel, getVal, view.w]);

  return (
    <section className="geo-workbench modern-atlas modern-minimal-edition" aria-label="Modern Şehir Boyalı Ticaret Haritası">
      {/* Üst Başlık ve Metrik Seçim Çubuğu */}
      <header className="advanced-heading minimal-header">
        <div>
          <div className="geo-title-row">
            <h3>Şehir Bazlı Ticaret ve Faaliyet Haritası</h3>
            <span className="geo-badge-live">
              {isCountryLevel
                ? 'Küresel Ülke Kloroplet Modu'
                : isCityZoomLevel
                ? 'Şehir İçi Detay Modu (Alıcı Noktaları Aktif)'
                : 'Şehir Havzaları Boyama Modu (Alıcılar Toplanmış)'}
            </span>
          </div>
          <p>
            {isCountryLevel
              ? 'Tüm dünya genelinde ülkelerin toplam ticaret hacmi ülke sınırlarıyla boyanır. Yakınlaşarak şehir havzalarını inceleyebilirsiniz.'
              : isCityZoomLevel
              ? 'Şehir boyutuna yaklaşıldı. Bu şehirdeki bireysel alıcı ve satış lokasyonları harita üzerinde noktalanmıştır.'
              : 'Nokta karmaşası olmadan şehir ve departman sınırları toplanmış alıcı hacmine göre boyanır. Şehir içine tıklandığında bireysel noktalar açılır.'}
          </p>
        </div>

        <div className="geo-header-actions">
          <label className="geo-metric-picker">
            Ölçüt
            <select aria-label="Harita ölçütü" value={metric} onChange={e => setMetric(e.target.value as typeof metric)}>
              <option value="sales">Net Satış (€)</option>
              <option value="profit">Brüt Kâr (€)</option>
              <option value="margin">Kâr Marjı (%)</option>
              <option value="customers">Alıcı / Müşteri Sayısı</option>
              <option value="returns">Toplam İade (€)</option>
            </select>
          </label>
        </div>
      </header>

      {/* Modern Yönetici Hızlı Kontrol Araç Çubuğu */}
      <div className="geo-tools minimal-toolbar">
        <div className="geo-focus-buttons">
          <button
            className={`btn-quick-focus ${!isCountryLevel && !isCityZoomLevel && view.w < 10 ? 'highlight' : ''}`}
            onClick={focusRhineCorridor}
            title="Şirketin ana damarı: Yukarı Ren ticaret koridoruna odaklan"
          >
            <span className="dot-pulse" />
            Ren Ticaret Koridoru (Ana Havza)
          </button>
          <button
            className={`btn-quick-focus ${!isCountryLevel && view.w >= 10 ? 'highlight' : ''}`}
            onClick={focusEuropeBasin}
            title="Avrupa bölgesel görünümü"
          >
            Avrupa (Şehirler Boyalı)
          </button>
          <button
            className={`btn-quick-focus ${isCountryLevel ? 'highlight' : ''}`}
            onClick={focusWorld}
            title="Küresel ülke kloroplet görünümü"
          >
            Dünya (Ülkeler Boyalı)
          </button>
        </div>

        <div className="geo-filter-group">
          <label>
            Ülke
            <select aria-label="Harita ülkesi" value={country} onChange={e => focusCountry(e.target.value)}>
              <option value="">Tüm Ülkeler</option>
              {world
                .filter(c => countryTotals.has(c.code))
                .sort((a, b) => trCountry(a.name).localeCompare(trCountry(b.name), 'tr'))
                .map(c => (
                  <option key={c.code} value={c.code}>
                    {trCountry(c.name)} · {money(countryTotals.get(c.code)?.sales || 0)}
                  </option>
                ))}
            </select>
          </label>

          <label>
            Şehir / Havza Odaklan
            <select
              aria-label="Harita şehri"
              value={selectedRegion ? `${selectedRegion.country}-${selectedRegion.code || selectedRegion.name}` : ''}
              onChange={e => {
                const reg = activeRegions.find(r => `${r.country}-${r.code || r.name}` === e.target.value);
                if (reg) {
                  setSelectedRegion(reg);
                  setSelectedPoint(null);
                  setCountry(reg.country);
                  // Şehir boyutuna yaklaştır (noktalar açılır)
                  const [cx, cy] = projectMercator(reg.center[0], reg.center[1]);
                  const w = 3.8;
                  const h = 2.5;
                  setView({
                    x: Math.max(0, Math.min(360 - w, cx - w / 2)),
                    y: Math.max(0, Math.min(180 - h, cy - h / 2)),
                    w,
                    h,
                  });
                  onFilter(reg.country, '', reg.cities.map(c => String(c.city)));
                } else {
                  setSelectedRegion(null);
                  setSelectedPoint(null);
                  onFilter(country ? String(rows.find(row => row.countryCode === country)?.country || '') : '');
                }
              }}
            >
              <option value="">Aktif Şehir / Departman Seçin</option>
              {activeRegions
                .filter(r => !country || r.country === country)
                .sort((a, b) => b.sales - a.sales)
                .map(r => (
                  <option key={`${r.country}-${r.code || r.name}`} value={`${r.country}-${r.code || r.name}`}>
                    {getRegionCityLabel(r)} ({trCountry(r.country)}) · {money(r.sales)} · {r.customers} Alıcı
                  </option>
                ))}
            </select>
          </label>
        </div>

        <div className="geo-zoom-controls">
          <button onClick={() => zoom(0.75)} title="Yakınlaştır (+)" aria-label="Yakınlaştır">
            +
          </button>
          <button onClick={() => zoom(1.3)} title="Uzaklaştır (−)" aria-label="Uzaklaştır">
            −
          </button>
        </div>
      </div>

      {/* YALIN VE MODERN SVG ATLAS KANVASI */}
      <div className="geo-canvas-container modern-glass-canvas" ref={containerRef} style={{ position: 'relative', overflow: 'hidden', userSelect: 'none', WebkitUserSelect: 'none' }}>
        {error ? (
          <p role="alert" className="geo-error">{error}</p>
        ) : !world.length ? (
          <div className="geo-loading">Kartografik sınırlar yükleniyor…</div>
        ) : (
          <svg
            ref={svgRef}
            className="geo-map modern-minimal-svg"
            viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`}
            role="group"
            aria-label="Şehir ve Ülke Boyalı Ticaret Haritası"
            tabIndex={0}
            style={{ userSelect: 'none', WebkitUserSelect: 'none' }}
            onPointerDown={e => {
              e.preventDefault();
              dragRef.current = {
                x: e.clientX,
                y: e.clientY,
                vx: view.x,
                vy: view.y,
                moved: false,
              };
              e.currentTarget.setPointerCapture(e.pointerId);
            }}
            onPointerMove={e => {
              if (!dragRef.current) return;
              const d = dragRef.current;
              const dx = e.clientX - d.x;
              const dy = e.clientY - d.y;
              if (Math.abs(dx) > 3 || Math.abs(dy) > 3) d.moved = true;
              const r = e.currentTarget.getBoundingClientRect();
              const scale = Math.min(r.width / view.w, r.height / view.h);

              setView(v => ({
                ...v,
                x: Math.max(0, Math.min(360 - v.w, d.vx - dx / scale)),
                y: Math.max(0, Math.min(180 - v.h, d.vy - dy / scale)),
              }));
            }}
            onPointerUp={() => {
              dragRef.current = null;
            }}
            onPointerCancel={() => {
              dragRef.current = null;
            }}
          >
            <defs>
              {/* Okyanus Zemin Degradesi */}
              <linearGradient id="minimalOcean" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#edf2f7" />
                <stop offset="100%" stopColor="#e2e8f0" />
              </linearGradient>

              {/* Lüks Rozet Gölgesi */}
              <filter id="glassPillShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0.08" stdDeviation="0.12" floodColor="#0f172a" floodOpacity="0.18" />
              </filter>

              {/* Parlak Vurgu */}
              <filter id="activeGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="0.25" floodColor="#10b981" floodOpacity="0.8" />
              </filter>
            </defs>

            {/* KATMAN 0: OKYANUS VE SAKİN MERİDYEN IZGARASI */}
            <rect x="0" y="0" width="360" height="180" fill="url(#minimalOcean)" />
            <g stroke="#cbd5e1" strokeWidth="0.04" strokeDasharray="0.8 0.8" opacity="0.4">
              {[30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map(lx => (
                <line key={`mer-${lx}`} x1={lx} y1="0" x2={lx} y2="180" />
              ))}
              {[30, 60, 90, 120, 150].map(ly => (
                <line key={`par-${ly}`} x1="0" y1={ly} x2="360" y2={ly} />
              ))}
            </g>

            {/* KATMAN 1: DÜNYA VE ÜLKE KARA KÜTLELERİ */}
            {/* Kural: Çok uzakta ise ülkeler boyanır; yakınlaştırıldığında nötr beyaz zemin kalır */}
            <g className="geo-base-countries">
              {worldPaths.map(c => {
                const cTotal = countryTotals.get(c.code);
                const hasCommercialPresence = Boolean(cTotal && cTotal.sales > 0);
                const isHovered = hoveredCountry === c.code;

                const countryFill = isCountryLevel
                  ? getCountryColor(cTotal ? getVal(cTotal) : 0)
                  : '#ffffff';

                return (
                  <path
                    key={`world-${c.code}`}
                    d={c.path}
                    fill={countryFill}
                    stroke={hasCommercialPresence ? '#64748b' : '#cbd5e1'}
                    strokeWidth={hasCommercialPresence ? Math.max(0.08, view.w / 600) : Math.max(0.04, view.w / 1000)}
                    vectorEffect="non-scaling-stroke"
                    style={{
                      cursor: isCountryLevel && hasCommercialPresence ? 'pointer' : 'default',
                      transition: 'fill 0.25s ease',
                      filter: isCountryLevel && isHovered ? 'url(#activeGlow)' : undefined,
                    }}
                    onPointerEnter={() => {
                      if (isCountryLevel && hasCommercialPresence) setHoveredCountry(c.code);
                    }}
                    onPointerLeave={() => {
                      if (isCountryLevel) setHoveredCountry(null);
                    }}
                    onClick={() => {
                      if (isCountryLevel && hasCommercialPresence) {
                        focusCountry(c.code);
                      }
                    }}
                  >
                    <title>{`${trCountry(c.name)}${cTotal ? ` · ${formatDisplay(getVal(cTotal))}` : ''}`}</title>
                  </path>
                );
              })}
            </g>

            {/* KATMAN 2: KULLANICI KURALI: "böyle kocaman noktalar yerine ülkelerin sınırları içerisinde ülkeler boyansın" */}
            {/* Ülke içi minimalist atlas etiketleri (Kocaman kutular/noktalar kaldırıldı, ülkeler kendi sınırlarında boyalı) */}
            {isCountryLevel &&
              worldCountryLabels.map(lbl => (
                <g
                  key={`country-lbl-${lbl.code}`}
                  transform={`translate(${lbl.cx}, ${lbl.cy})`}
                  pointerEvents="none"
                >
                  {/* Şık ve Zarif Ülke Adı (Kutusuz, Halo Konturlu) */}
                  <text
                    x={0}
                    y={0}
                    textAnchor="middle"
                    fill="#0f172a"
                    fontSize={lbl.fontSz}
                    fontWeight="800"
                    letterSpacing="0.08em"
                    fontFamily="system-ui, -apple-system, sans-serif"
                    style={{
                      paintOrder: 'stroke fill',
                      stroke: '#ffffff',
                      strokeWidth: `${lbl.fontSz * 0.32}px`,
                      strokeLinejoin: 'round',
                      textTransform: 'uppercase',
                    }}
                  >
                    {lbl.name}
                  </text>
                  {/* Ciro Rakamı */}
                  <text
                    x={0}
                    y={lbl.fontSz * 1.15}
                    textAnchor="middle"
                    fill="#047857"
                    fontSize={lbl.fontSz * 0.85}
                    fontWeight="800"
                    fontFamily="system-ui, -apple-system, sans-serif"
                    style={{
                      paintOrder: 'stroke fill',
                      stroke: '#ffffff',
                      strokeWidth: `${lbl.fontSz * 0.26}px`,
                      strokeLinejoin: 'round',
                    }}
                  >
                    {lbl.valStr}
                  </text>
                </g>
              ))}

            {/* KATMAN 3: KULLANICI KURALI: "nokta değil şehirleri boyamalıyız, alıcılar toplanmalı" */}
            {/* ŞEHİRLER / DEPARTMANLAR BOYANIYOR (Uzakta ülke, yakında şehir poligonları) */}
            {!isCountryLevel && (
              <g className="geo-active-regions">
                {activeRegions.map(reg => {
                  const val = getVal(reg);
                  const fillColor = getRegionColor(val);
                  const isSelected = selectedRegion === reg;
                  const isHovered = hoveredRegion === reg;

                  // Eğer şehir boyutuna büyütülmüşse, poligon şeffaf bir zemin olur (noktalar rahat görünsün)
                  const polyFillOpacity = isCityZoomLevel
                    ? isSelected ? 0.22 : 0.12
                    : isSelected ? 0.95 : isHovered ? 0.90 : 0.82;

                  return (
                    <path
                      key={`active-reg-${reg.country}-${reg.code || reg.name}`}
                      d={reg.path}
                      fill={fillColor}
                      fillOpacity={polyFillOpacity}
                      stroke={isSelected ? '#0f172a' : isHovered ? '#059669' : '#047857'}
                      strokeWidth={isSelected ? Math.max(0.18, view.w / 400) : isHovered ? Math.max(0.14, view.w / 500) : Math.max(0.08, view.w / 800)}
                      vectorEffect="non-scaling-stroke"
                      className={`active-region-path ${isSelected ? 'selected' : ''}`}
                      style={{
                        cursor: 'pointer',
                        transition: 'fill-opacity 0.2s, stroke-width 0.2s',
                        filter: (isHovered || isSelected) && !isCityZoomLevel ? 'url(#activeGlow)' : undefined,
                      }}
                      onPointerEnter={() => setHoveredRegion(reg)}
                      onPointerLeave={() => setHoveredRegion(null)}
                      onClick={() => {
                        setSelectedRegion(reg);
                        setSelectedPoint(null);
                        const [cx, cy] = projectMercator(reg.center[0], reg.center[1]);
                        const w = 3.8;
                        const h = 2.5;
                        setView({
                          x: Math.max(0, Math.min(360 - w, cx - w / 2)),
                          y: Math.max(0, Math.min(180 - h, cy - h / 2)),
                          w,
                          h,
                        });
                        onFilter(reg.country, '', reg.cities.map(c => String(c.city)));
                      }}
                    >
                      <title>{`${getRegionCityLabel(reg)} (${trCountry(reg.country)}) · ${formatDisplay(val)} · ${reg.customers} Alıcı`}</title>
                    </path>
                  );
                })}
              </g>
            )}

            {/* KATMAN 4: ŞEHİR POLİGONLARI ÜZERİNDEKİ YALIN BİLGİ ETİKETLERİ (NORMAL BÖLGE GÖRÜNÜMÜ) */}
            {!isCountryLevel && !isCityZoomLevel &&
              regionBadges.map(({ reg, cx, cy, label, valStr, custStr, badgeW, badgeH, fontSz }) => {
                const isSelected = selectedRegion === reg;
                const isHovered = hoveredRegion === reg;

                return (
                  <g
                    key={`reg-label-${reg.country}-${reg.code || reg.name}`}
                    transform={`translate(${cx}, ${cy})`}
                    pointerEvents="none"
                    filter="url(#glassPillShadow)"
                  >
                    <rect
                      x={-badgeW / 2}
                      y={-badgeH / 2}
                      width={badgeW}
                      height={badgeH}
                      rx={badgeH / 2}
                      ry={badgeH / 2}
                      fill={isSelected ? '#0f172a' : '#ffffff'}
                      fillOpacity={isSelected ? 0.98 : 0.95}
                      stroke={isSelected ? '#38bdf8' : isHovered ? '#059669' : '#94a3b8'}
                      strokeWidth={Math.max(0.02, view.w / 1200)}
                    />
                    <circle cx={-badgeW / 2 + fontSz * 1.0} cy={0} r={fontSz * 0.28} fill={isSelected ? '#38bdf8' : '#10b981'} />
                    <text
                      x={-badgeW / 2 + fontSz * 1.8}
                      y={fontSz * 0.35}
                      textAnchor="start"
                      fill={isSelected ? '#ffffff' : '#0f172a'}
                      fontSize={fontSz * 0.88}
                      fontWeight="700"
                      fontFamily="system-ui, sans-serif"
                    >
                      {label}
                    </text>
                    <text
                      x={badgeW / 2 - fontSz * 1.0}
                      y={fontSz * 0.35}
                      textAnchor="end"
                      fill={isSelected ? '#7dd3fc' : '#047857'}
                      fontSize={fontSz * 0.88}
                      fontWeight="800"
                      fontFamily="system-ui, sans-serif"
                    >
                      {valStr}
                    </text>
                  </g>
                );
              })}

            {/* KATMAN 5: KULLANICI KURALI: "eğer yeterince büyütülüp şehir boyutuna gelirse o zaman noktalar gelsin" */}
            {isCityZoomLevel && (
              <g className="geo-local-points">
                {localCityPoints.map((pt, ptIdx) => {
                  const isSelected = selectedPoint === pt;
                  const isHovered = hoveredPoint === pt;
                  const baseR = Math.max(0.025, Math.min(0.075, (Math.log10(pt.sales + 10) / 6.0) * (view.w * 0.018)));
                  const r = isSelected || isHovered ? baseR * 1.4 : baseR;
                  const ptColor = getRegionColor(pt.sales);
                  const fontSz = Math.max(0.038, view.w * 0.011);
                  // Çakışmayı önlemek için sadece en yüksek cirolu ilk 5 merkezde veya seçili/hover olanlarda kalıcı etiket göster
                  const showLabel = isSelected || isHovered || ptIdx < 5 || pt.sales >= 20000;

                  return (
                    <g
                      key={`pt-${pt.country}-${pt.city}`}
                      transform={`translate(${pt.px}, ${pt.py})`}
                      style={{ cursor: 'pointer' }}
                      onPointerEnter={() => setHoveredPoint(pt)}
                      onPointerLeave={() => setHoveredPoint(null)}
                      onClick={() => {
                        setSelectedPoint(pt);
                        onFilter(pt.country, pt.city);
                      }}
                    >
                      {/* Dış Halka & Nabız */}
                      <circle
                        r={r * 1.7}
                        fill={ptColor}
                        fillOpacity={isSelected || isHovered ? 0.35 : 0.15}
                        stroke={ptColor}
                        strokeOpacity={0.5}
                        strokeWidth={Math.max(0.005, view.w / 2000)}
                      />
                      {/* Nokta Çekirdeği */}
                      <circle
                        r={r}
                        fill={ptColor}
                        stroke="#ffffff"
                        strokeWidth={Math.max(0.006, view.w / 1600)}
                      />

                      {/* Şehir İçi Nokta Etiketi (Kompakt ve Zarif) */}
                      {showLabel && (
                        <text
                          x={0}
                          y={-r - fontSz * 0.35}
                          textAnchor="middle"
                          fill="#0f172a"
                          fontSize={fontSz}
                          fontWeight="700"
                          fontFamily="system-ui, sans-serif"
                          style={{ paintOrder: 'stroke', stroke: '#ffffff', strokeWidth: '0.012px' }}
                        >
                          {pt.name}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            )}

            {/* Seçili veya Üzerine Gelinmiş Noktanın Zengin Rozeti */}
            {isCityZoomLevel && (hoveredPoint || selectedPoint) && (
              <g
                transform={`translate(${(hoveredPoint || selectedPoint)!.px}, ${(hoveredPoint || selectedPoint)!.py - 0.22})`}
                pointerEvents="none"
                filter="url(#glassPillShadow)"
              >
                {(() => {
                  const targetPt = (hoveredPoint || selectedPoint)!;
                  const fontSz = Math.max(0.045, view.w * 0.013);
                  const valStr = formatDisplay(targetPt.sales);
                  const custStr = `${targetPt.customers} Alıcı · ${targetPt.invoices} Fatura`;
                  const label = `${targetPt.name} · ${valStr} (${custStr})`;
                  const badgeW = label.length * fontSz * 0.46 + fontSz * 2.8;
                  const badgeH = fontSz * 2.3;

                  return (
                    <>
                      <rect
                        x={-badgeW / 2}
                        y={-badgeH / 2}
                        width={badgeW}
                        height={badgeH}
                        rx={badgeH / 2}
                        ry={badgeH / 2}
                        fill="#0f172a"
                        fillOpacity="0.96"
                        stroke="#38bdf8"
                        strokeWidth={Math.max(0.03, view.w / 1000)}
                      />
                      <circle cx={-badgeW / 2 + fontSz * 1.0} cy={0} r={fontSz * 0.28} fill="#34d399" />
                      <text
                        x={-badgeW / 2 + fontSz * 1.8}
                        y={fontSz * 0.35}
                        textAnchor="start"
                        fill="#ffffff"
                        fontSize={fontSz * 0.88}
                        fontWeight="700"
                        fontFamily="system-ui, sans-serif"
                      >
                        {targetPt.name}
                      </text>
                      <text
                        x={badgeW / 2 - fontSz * 1.0}
                        y={fontSz * 0.35}
                        textAnchor="end"
                        fill="#7dd3fc"
                        fontSize={fontSz * 0.88}
                        fontWeight="800"
                        fontFamily="system-ui, sans-serif"
                      >
                        {valStr} ({custStr})
                      </text>
                    </>
                  );
                })()}
              </g>
            )}
          </svg>
        )}

        {/* HARİTA İÇİ YÖNETİCİ BİLGİ KARTI (FLOATING EXECUTIVE HUD) */}
        <div className="geo-floating-hud">
          <div className="hud-metric-row">
            <span className="hud-indicator-dot" />
            <strong>Odak Havza:</strong>
            <span>
              {isCountryLevel
                ? 'Tüm Dünya (Kloroplet)'
                : isCityZoomLevel
                ? `${selectedRegion ? getRegionCityLabel(selectedRegion) : 'Şehir İçi Noktalar'}`
                : 'Yukarı Ren & Grand-Est'}
            </span>
          </div>
          <div className="hud-stats-row">
            <span>€1.40M Net Satış</span>
            <small>·</small>
            <span>{isCityZoomLevel ? `${localCityPoints.length} Lokasyon Noktası` : `${activeRegions.length} Şehir Havzası`}</span>
            <small>·</small>
            <span>81 Alıcı</span>
          </div>
        </div>

        {/* Hover / Detay Bilgilendirme Rozeti (Sol Alt) */}
        {(hoveredRegion || hoveredPoint) && (
          <div className="geo-hover-pill">
            <span>
              {hoveredPoint
                ? `${hoveredPoint.name} (${hoveredPoint.regionName})`
                : `${getRegionCityLabel(hoveredRegion!)} (${trCountry(hoveredRegion!.country)})`}
            </span>
            <strong>
              {formatDisplay(hoveredPoint ? hoveredPoint.sales : getVal(hoveredRegion!))}
              <small style={{ marginLeft: 6, fontWeight: 500, opacity: 0.9 }}>
                ({hoveredPoint ? `${hoveredPoint.customers} Alıcı` : `${hoveredRegion!.customers} Alıcı Toplamı`})
              </small>
            </strong>
          </div>
        )}
      </div>

      {/* Lejant (Eşik Renk Tonları Göstergesi) */}
      <div className="choropleth-legend-bar minimal-legend">
        <span className="legend-title">
          {isCountryLevel
            ? 'Ülke Toplamı Eşiği:'
            : metric === 'sales'
            ? 'Şehir Net Satış Tonları:'
            : metric === 'returns'
            ? 'İade Oranı:'
            : 'Performans Tonu:'}
        </span>
        <div className="legend-items">
          <div className="legend-step">
            <span className="step-color" style={{ background: '#ffffff', border: '1px solid #cbd5e1' }} />
            <span className="step-label">Satış Yok (Nötr Ülke)</span>
          </div>
          {(metric === 'returns'
            ? RETURN_PALETTE
            : isCountryLevel
            ? COUNTRY_CHOROPLETH_PALETTE
            : REGION_EMERALD_PALETTE
          ).map((color, idx) => (
            <div key={color} className="legend-step">
              <span className="step-color" style={{ background: color }} />
              <span className="step-label">
                {idx === 0 ? 'Düşük Hacim' : idx === 5 ? 'Zirve Merkez (Strazburg/Müluz)' : `${idx + 1}. Kademe`}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Seçili Şehir / Havza Yönetim Kartı */}
      {(selectedRegion || selectedPoint) && (
        <div className="geo-selection modern-card minimal-card">
          <div className="geo-selection-header">
            <h4>
              {selectedPoint
                ? `${selectedPoint.name} (${selectedPoint.regionName}) · Bireysel Lokasyon Kartı`
                : `${getRegionCityLabel(selectedRegion!)} (${trCountry(selectedRegion!.country)}) · Şehir Havza Kartı`}
            </h4>
            <button
              onClick={() => {
                setSelectedRegion(null);
                setSelectedPoint(null);
                onFilter(country ? String(rows.find(row => row.countryCode === country)?.country || '') : '');
              }}
            >
              Seçimi Temizle
            </button>
          </div>
          <div className="geo-selection-metrics">
            <div>
              <span>Net Satış</span>
              <strong>{money(selectedPoint ? selectedPoint.sales : selectedRegion!.sales)}</strong>
            </div>
            <div>
              <span>Brüt Kâr</span>
              <strong>{money(selectedPoint ? selectedPoint.profit : selectedRegion!.profit)}</strong>
            </div>
            <div>
              <span>Kâr Marjı</span>
              <strong>
                %{number(
                  selectedPoint
                    ? (selectedPoint.profit / (selectedPoint.sales || 1)) * 100
                    : selectedRegion!.margin || 0,
                  1
                )}
              </strong>
            </div>
            <div>
              <span>Toplam Alıcı</span>
              <strong>{selectedPoint ? selectedPoint.customers : selectedRegion!.customers} Alıcı</strong>
            </div>
            <div>
              <span>İade Tutarı</span>
              <strong className="text-negative">{money(selectedPoint ? selectedPoint.returns : selectedRegion!.returns)}</strong>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
