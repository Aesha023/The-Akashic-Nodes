import React from 'react';

export const FlowingWaterBg: React.FC<{ children?: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      {/* Background Animated Contours */}
      <div
        className="absolute inset-0 pointer-events-none select-none overflow-hidden opacity-60"
        aria-hidden="true"
      >
        <svg
          className="absolute -top-[20%] -left-[10%] w-[130%] h-[140%] text-brand/[0.04]"
          viewBox="0 0 1440 900"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Elevation contour line 1 */}
          <path
            d="M-100 250 C 300 180, 600 350, 1000 220 C 1200 150, 1400 280, 1600 240"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeDasharray="6 4"
            className="animate-[pulse_8s_ease-in-out_infinite]"
          />
          {/* Elevation contour line 2 */}
          <path
            d="M-100 340 C 250 290, 550 420, 950 300 C 1250 220, 1450 380, 1600 330"
            stroke="currentColor"
            strokeWidth="2.2"
          />
          {/* Elevation contour line 3 */}
          <path
            d="M-100 450 C 200 390, 500 500, 900 400 C 1300 310, 1500 470, 1600 420"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeDasharray="8 6"
          />
          {/* Elevation contour line 4 (River Thalweg) */}
          <path
            d="M-100 580 C 180 500, 480 620, 880 510 C 1220 420, 1480 580, 1600 540"
            stroke="rgba(10, 102, 255, 0.08)"
            strokeWidth="3.5"
          />
          {/* Elevation contour line 5 */}
          <path
            d="M-100 700 C 150 630, 450 740, 820 630 C 1180 530, 1420 690, 1600 660"
            stroke="currentColor"
            strokeWidth="1.8"
          />
        </svg>

        {/* Soft Radial Ambient Glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-brand/[0.03] rounded-full blur-3xl pointer-events-none" />
      </div>

      <div className="relative z-10">{children}</div>
    </div>
  );
};
