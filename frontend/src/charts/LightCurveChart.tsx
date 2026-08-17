import React from 'react';
import Plot from 'react-plotly.js';

interface LightCurveProps {
  time: number[];
  flux: number[];
  phase?: number[];
  foldedFlux?: number[];
  inTransitMask?: number[];
  title?: string;
  type: 'timeseries' | 'phase_folded';
}

const LightCurveChart: React.FC<LightCurveProps> = ({ 
  time, 
  flux, 
  phase,
  foldedFlux,
  inTransitMask, 
  title = "Light Curve",
  type
}) => {
  const commonLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#9CA3AF', family: 'Inter' },
    margin: { t: 40, r: 20, l: 60, b: 40 },
    showlegend: true,
    legend: { orientation: 'h' as const, y: 1.1 },
    xaxis: { 
      gridcolor: '#1E2532',
      zerolinecolor: '#1E2532',
      title: type === 'timeseries' ? 'Time (days)' : 'Phase',
    },
    yaxis: { 
      gridcolor: '#1E2532',
      zerolinecolor: '#1E2532',
      title: 'Relative Flux',
    },
  };

  const getData = () => {
    if (type === 'timeseries') {
      // Split points into transit and non-transit if mask is provided
      if (inTransitMask && inTransitMask.length > 0) {
        const mask = new Set(inTransitMask);
        
        const transitTime: number[] = [];
        const transitFlux: number[] = [];
        const normalTime: number[] = [];
        const normalFlux: number[] = [];

        time.forEach((t, i) => {
          if (mask.has(i)) {
            transitTime.push(t);
            transitFlux.push(flux[i]);
          } else {
            normalTime.push(t);
            normalFlux.push(flux[i]);
          }
        });

        return [
          {
            x: normalTime,
            y: normalFlux,
            mode: 'markers',
            type: 'scatter',
            name: 'Out of Transit',
            marker: { color: '#4B5563', size: 3 }, // text_muted
          },
          {
            x: transitTime,
            y: transitFlux,
            mode: 'markers',
            type: 'scatter',
            name: 'In Transit',
            marker: { color: '#F87171', size: 5 }, // danger (red)
          }
        ];
      }

      // Default single trace
      return [{
        x: time,
        y: flux,
        mode: 'markers',
        type: 'scatter',
        name: 'Flux',
        marker: { color: '#38BDF8', size: 3 }, // primary
      }];
    } 
    
    // Phase folded
    if (phase && foldedFlux) {
      return [{
        x: phase,
        y: foldedFlux,
        mode: 'markers',
        type: 'scatter',
        name: 'Folded Flux',
        marker: { color: '#818CF8', size: 4 }, // accent
      }];
    }

    return [];
  };

  return (
    <div className="w-full h-[400px]">
      <Plot
        data={getData() as any}
        layout={{ ...commonLayout, title: { text: title, font: { size: 14 } } }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default LightCurveChart;
