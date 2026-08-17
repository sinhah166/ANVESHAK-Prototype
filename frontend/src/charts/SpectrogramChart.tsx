import React from 'react';
import Plot from 'react-plotly.js';

interface SpectrogramProps {
  spectrogram: number[][];
  frequencies: number[];
  times: number[];
  title?: string;
}

const SpectrogramChart: React.FC<SpectrogramProps> = ({ 
  spectrogram, 
  frequencies, 
  times,
  title = "Dynamic Spectrum" 
}) => {
  const layout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#9CA3AF', family: 'Inter' },
    margin: { t: 40, r: 20, l: 60, b: 40 },
    title: { text: title, font: { size: 14 } },
    xaxis: { 
      title: 'Time (s)',
      gridcolor: '#1E2532',
      zerolinecolor: '#1E2532',
    },
    yaxis: { 
      title: 'Frequency (MHz)',
      gridcolor: '#1E2532',
      zerolinecolor: '#1E2532',
    },
  };

  return (
    <div className="w-full h-[400px]">
      <Plot
        data={[{
          z: spectrogram, // Z is expected to be [y][x], check transpose if needed
          x: times,
          y: frequencies,
          type: 'heatmap',
          colorscale: 'Viridis', // Scientific color scale
          colorbar: { title: 'Intensity (S/N)', titleside: 'right' }
        }]}
        layout={layout}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default SpectrogramChart;
