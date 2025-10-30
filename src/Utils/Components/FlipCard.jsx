import React, { useState, useRef } from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { toPng } from 'html-to-image';

const FlipCard = ({ title, itemFront, itemBack, styleNow = {} }) => {
  const [flipped, setFlipped] = useState(false);
  const cardRef = useRef(null);

  // Refs for the two faces (we'll capture the currently visible one)
  const frontRef = useRef(null);
  const backRef = useRef(null);

  // (Optional helper) Ensure overflow is visible during capture for deep children
  const makeAllVisibleAndResize = (node) => {
    const traverse = (element) => {
      element.style.overflow = 'visible';
      Array.from(element.children).forEach(child => {
        if (child instanceof HTMLElement) traverse(child);
      });
    };
    if (node) traverse(node);
  };

  // OPTION B: capture only the visible face and neutralize its transform
  const takeScreenshot = async () => {
    const face = flipped ? backRef.current : frontRef.current;
    if (!face) return;

    // If your face has clipped content inside, this helps ensure it's not hidden
    makeAllVisibleAndResize(face);

    // Measure current visible size
    const rect = face.getBoundingClientRect();

    try {
      const dataUrl = await toPng(face, {
        cacheBust: true,
        backgroundColor: '#ffffff',
        pixelRatio: window.devicePixelRatio,
        width: Math.round(rect.width),
        height: Math.round(rect.height),

        // Apply inline styles to the cloned root (the face) to avoid mirrored output
        style: {
          transform: 'none',
          backfaceVisibility: 'visible',
          WebkitBackfaceVisibility: 'visible',
          position: 'static', // avoids absolute-stacking artifacts
        },
      });

      const link = document.createElement('a');
      link.download = `${title}-${flipped ? 'back' : 'front'}.png`;
      link.href = dataUrl;
      link.click();
    } catch (error) {
      console.error('Screenshot failed:', error);
    }
  };

  if (!styleNow['width']) styleNow['width'] = '49%';

  return (
    <Card
      title={title}
      className="p-shadow-4 w3-center"
      style={{ ...styleNow, overflow: 'hidden', borderRadius: '12px' }}
    >
      <div className={`flip-card-container ${flipped ? 'flipped' : ''}`} ref={cardRef}>
        <div className="flip-card">
          <div className="flip-card-front" ref={frontRef}>
            {itemFront}
          </div>
          <div className="flip-card-back" ref={backRef}>
            {itemBack}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
        <Button label="Flip" icon="pi pi-refresh" onClick={() => setFlipped(v => !v)} />
        <Button label="Take Screenshot" icon="pi pi-camera" onClick={takeScreenshot} />
      </div>
    </Card>
  );
};

export default FlipCard;
