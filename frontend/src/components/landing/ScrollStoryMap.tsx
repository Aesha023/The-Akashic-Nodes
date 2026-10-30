import React, { useState } from 'react';
import { 
  ChevronRight, 
  ChevronLeft
} from 'lucide-react';
import { GangaMap } from '../map/GangaMap';
import { Button } from '../common/Button';

interface StoryStep {
  step: number;
  badge: string;
  question: string;
  title: string;
  description: string;
  kpi: {
    label: string;
    value: string;
    unit?: string;
    source: string;
  };
  layerState: {
    extent: boolean;
    evac: boolean;
  };
}

export const ScrollStoryMap: React.FC = () => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const steps: StoryStep[] = [
    {
      step: 1,
      badge: 'Step 1 · Geography',
      question: 'Where is the dam located and what is the terrain setting?',
      title: 'Rishikesh Valley Reach (Uttarakhand)',
      description: 'The target simulation reach spans 5x5 km of the Himalayan foothills along the Ganga river gorge. Elevation drops through a steep V-shaped canyon flanked by 400m rocky mountain slopes.',
      kpi: {
        label: 'Domain Bounding AOI',
        value: '5x5 km',
        unit: '25 km²',
        source: 'Copernicus GLO-30 DEM · EPSG:32644',
      },
      layerState: {
        extent: false,
        evac: false,
      },
    },
    {
      step: 2,
      badge: 'Step 2 · Breach Discharge',
      question: 'How much water discharges through the dam breach?',
      title: 'Froehlich Breach Forcing Initiated',
      description: 'The scenario simulates an emergency earthen dam-break event with an assumed breach inflow peak of 5,000.0 m³/s, derived via Froehlich (2008) empirical back-solve.',
      kpi: {
        label: 'Assumed breach inflow (scenario input)',
        value: '5,000.0',
        unit: 'm³/s',
        source: 'Froehlich (2008) · VALIDATION §11.1',
      },
      layerState: {
        extent: true,
        evac: false,
      },
    },
    {
      step: 3,
      badge: 'Step 3 · Inundation Depth',
      question: 'How far does the water spread, and how deep does it get?',
      title: 'Tier-0 Static Screening Envelope',
      description: 'Water fills 1,918 cells across 1.72 km² of valley floor. Depths reach up to 7.73 m along the primary channel thalweg, with 82.1% of inundated area exceeding 1.5 m depth.',
      kpi: {
        label: 'Maximum Inundation Depth',
        value: '7.73',
        unit: 'm',
        source: 'Depth above DEM water surface; true channel depth is greater.',
      },
      layerState: {
        extent: true,
        evac: false,
      },
    },
    {
      step: 4,
      badge: 'Step 4 · Vulnerable Assets',
      question: 'Which roads and buildings are flooded?',
      title: 'Infrastructure & Population Exposure',
      description: '17.34 km of roadway are submerged, severing critical valley links. 5 buildings are flooded, while all 28 hospitals and police thanas on high river bluffs remain completely safe.',
      kpi: {
        label: 'Severed Road Network',
        value: '17.34',
        unit: 'km (10.9%)',
        source: 'OpenStreetMap Snapshot 2026-10-22 · VALIDATION §11.3',
      },
      layerState: {
        extent: true,
        evac: false,
      },
    },
    {
      step: 5,
      badge: 'Step 5 · Evacuation',
      question: 'How do people escape to high ground safely?',
      title: 'Dijkstra Shortest-Path Evacuation Corridors',
      description: 'Non-severed road segments form active safe corridors (emerald green lines with white casings). 2 building clusters have immediate high-ground access; 3 cut-off structures are marked for aerial/boat rescue.',
      kpi: {
        label: 'Safe Evacuation Routes',
        value: '2 of 5',
        unit: 'origins reached',
        source: 'OSMnx Directed Graph Routing · VALIDATION §11.4',
      },
      layerState: {
        extent: true,
        evac: true,
      },
    },
  ];

  const current = steps[currentStepIndex];

  return (
    <div className="w-full bg-white rounded-2xl border border-border shadow-md overflow-hidden">
      {/* Top Progress Track */}
      <div className="flex border-b border-border bg-bg-subtle divide-x divide-border overflow-x-auto">
        {steps.map((s, idx) => (
          <button
            key={s.step}
            onClick={() => setCurrentStepIndex(idx)}
            className={`flex-1 py-3 px-3 text-left transition-colors whitespace-nowrap min-w-[140px] ${
              currentStepIndex === idx
                ? 'bg-white border-b-2 border-b-brand'
                : 'hover:bg-bg-muted text-text-tertiary'
            }`}
          >
            <span
              className={`text-[10px] font-semibold uppercase tracking-wider block ${
                currentStepIndex === idx ? 'text-brand' : 'text-text-tertiary'
              }`}
            >
              Phase {s.step}
            </span>
            <span
              className={`text-xs font-semibold truncate block mt-0.5 ${
                currentStepIndex === idx ? 'text-text' : 'text-text-secondary'
              }`}
            >
              {s.badge.split('·')[1]?.trim() || s.title}
            </span>
          </button>
        ))}
      </div>

      {/* Main Split Layout: Map on Right, Story Narrative on Left */}
      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[500px]">
        {/* Left Narrative Column */}
        <div className="lg:col-span-5 p-6 sm:p-8 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-border bg-white">
          <div className="space-y-4">
            {/* Plain English Question for Government Users (Requirement A) */}
            <div className="p-3 rounded-xl bg-brand-soft border border-brand/20">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-brand">
                Government Officer Question:
              </p>
              <p className="text-sm sm:text-base font-bold text-text mt-0.5">
                "{current.question}"
              </p>
            </div>

            <div>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-bg-muted text-text-secondary">
                {current.badge}
              </span>
              <h3 className="text-2xl font-bold tracking-tight text-text mt-2">
                {current.title}
              </h3>
              <p className="text-sm sm:text-base text-text-secondary mt-2.5 leading-relaxed">
                {current.description}
              </p>
            </div>

            {/* KPI Stat Tile with Mandatory Source */}
            <div className="p-4 rounded-xl bg-bg-subtle border border-border">
              <p className="text-[11px] font-semibold text-text-tertiary uppercase tracking-wider">
                {current.kpi.label}
              </p>
              <div className="flex items-baseline gap-1.5 mt-1">
                <span className="text-3xl font-bold text-text tabular-nums font-mono">
                  {current.kpi.value}
                </span>
                {current.kpi.unit && (
                  <span className="text-sm font-semibold text-text-secondary">
                    {current.kpi.unit}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-text-tertiary mt-2 pt-2 border-t border-border/80 flex items-center gap-1 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-brand/50"></span>
                <span>{current.kpi.source}</span>
              </p>
            </div>
          </div>

          {/* Step Navigation Controls */}
          <div className="flex items-center justify-between pt-6 mt-6 border-t border-border">
            <Button
              variant="secondary"
              size="sm"
              disabled={currentStepIndex === 0}
              onClick={() => setCurrentStepIndex((prev) => Math.max(0, prev - 1))}
              icon={<ChevronLeft size={16} />}
            >
              Previous
            </Button>

            <span className="text-xs font-mono text-text-tertiary">
              Step {currentStepIndex + 1} of {steps.length}
            </span>

            <Button
              variant="primary"
              size="sm"
              disabled={currentStepIndex === steps.length - 1}
              onClick={() => setCurrentStepIndex((prev) => Math.min(steps.length - 1, prev + 1))}
              icon={<ChevronRight size={16} />}
              iconPosition="right"
            >
              Next Phase
            </Button>
          </div>
        </div>

        {/* Right Map Canvas */}
        <div className="lg:col-span-7 bg-[#EFF1F5] relative min-h-[420px] lg:min-h-full">
          <GangaMap
            height="100%"
            interactive={true}
            showControls={true}
            showEvacuation={current.layerState.evac}
          />
        </div>
      </div>
    </div>
  );
};
